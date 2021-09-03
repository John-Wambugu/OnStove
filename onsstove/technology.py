import os
import geopandas as gpd
import re
import pandas as pd
import numpy as np
import datetime
from math import exp

from .raster import *


class Technology:
    """
    Standard technology class.
    """

    def __init__(self,
                 name=None,
                 carbon_intensity=0,
                 energy_content=0,
                 tech_life=0,  # in years
                 inv_cost=0,  # in USD
                 infra_cost=0,  # cost of additional infrastructure
                 fuel_cost=0,
                 time_of_cooking=0,
                 om_cost=0,  # percentage of investement cost
                 efficiency=0,  # ratio
                 pm25=0):  # 24-h PM2.5 concentration

        self.name = name
        self.carbon_intensity = carbon_intensity
        self.energy_content = energy_content
        self.tech_life = tech_life
        self.fuel_cost = fuel_cost
        self.inv_cost = inv_cost
        self.infra_cost = infra_cost
        self.om_cost = om_cost
        self.time_of_cooking = time_of_cooking
        self.efficiency = efficiency
        self.pm25 = pm25
        self.time_of_collection = None
        self.fuel_use = None

    def __setitem__(self, idx, value):
        if idx == 'name':
            self.name = value
        elif idx == 'energy_content':
            self.energy_content = value
        elif idx == 'carbon_intensity':
            self.carbon_intensity = value
        elif idx == 'fuel_cost':
            self.fuel_cost = value
        elif idx == 'tech_life':
            self.tech_life = value
        elif idx == 'inv_cost':
            self.inv_cost = value
        elif idx == 'infra_cost':
            self.infra_cost = value
        elif idx == 'om_cost':
            self.om_cost = value
        elif idx == 'time_of_cooking':
            self.time_of_cooking = value
        elif idx == 'efficiency':
            self.efficiency = value
        elif idx == 'pm25':
            self.pm25 = value
        elif idx == 'time_of_collection':
            self.time_of_collection = value
        elif idx == 'fuel_use':
            self.fuel_use = value
        else:
            raise KeyError(idx)

    def relative_risk(self):
        if self.pm25 < 7.298:
            rr_alri = 1
        else:
            rr_alri = 1 + 2.383 * (1 - exp(-0.004 * (self.pm25 - 7.298) ** 1.193))

        if self.pm25 < 7.337:
            rr_copd = 1
        else:
            rr_copd = 1 + 22.485 * (1 - exp(-0.001 * (self.pm25 - 7.337) ** 0.694))

        if self.pm25 < 7.505:
            rr_ihd = 1
        else:
            rr_ihd = 1 + 2.538 * (1 - exp(-0.081 * (self.pm25 - 7.505) ** 0.466))

        if self.pm25 < 7.345:
            rr_lc = 1
        else:
            rr_lc = 1 + 152.496 * (1 - exp(-0.000167 * (self.pm25 - 7.345) ** 0.76))

        return rr_alri, rr_copd, rr_ihd, rr_lc

    @classmethod
    def paf(self, rr, sfu):

        paf = (sfu * (rr - 1)) / (sfu * (rr - 1) + 1)

        return paf

    @staticmethod
    def discount_factor(self, specs_file):
        '''

        :param self:
        :param specs_file: social specs file
        :return: discount factor to be used for all costs in the net benefit fucntion and the years of analysis
        '''
        if specs_file["Start_year"] == specs_file["End_year"]:
            proj_life = 1
        else:
            proj_life = specs_file["End_year"] - specs_file["Start_year"]

        year = np.arange(proj_life)

        discount_factor = (1 + specs_file["Discount_rate_tech"]) ** year

        return discount_factor, proj_life

    def mortality(self, social_specs_file, paf_0_alri, paf_0_copd, paf_0_lc, paf_0_ihd):
        """
        Calculates mortality rate per fuel

        Returns
        ----------
        Monetary mortality for each stove in urban and rural settings
        """

        rr_alri, rr_copd, rr_ihd, rr_lc = self.relative_risk()

        paf_alri = self.paf(rr_alri, sfu)
        paf_copd = self.paf(rr_copd, sfu)
        paf_ihd = self.paf(rr_ihd, sfu)
        paf_lc = self.paf(rr_lc, sfu)

        mort_alri_U = social_specs_file["Urban_Hhsize"] * (paf_0_alri - paf_alri) * social_specs_file["Mort_ALRI"]
        mort_copd_U = social_specs_file["Urban_Hhsize"] * (paf_0_copd - paf_copd) * social_specs_file["Mort_COPD"]
        mort_ihd_U = social_specs_file["Urban_Hhsize"] * (paf_0_ihd - paf_ihd) * social_specs_file["Mort_IHD"]
        mort_lc_U = social_specs_file["Urban_Hhsize"] * paf_lc * social_specs_file["Mort_LC"]

        mort_alri_R = social_specs_file["Rural_Hhsize"] * (paf_0_alri - paf_alri) * social_specs_file["Mort_ALRI"]
        mort_copd_R = social_specs_file["Rural_Hhsize"] * (paf_0_copd - paf_copd) * social_specs_file["Mort_COPD"]
        mort_ihd_R = social_specs_file["Rural_Hhsize"] * (paf_0_ihd - paf_ihd) * social_specs_file["Mort_IHD"]
        mort_lc_R = social_specs_file["Rural_Hhsize"] * (paf_0_lc - paf_lc) * social_specs_file["Mort_LC"]

        cl_copd = {1: 0.3, 2: 0.2, 3: 0.17, 4: 0.17, 5: 0.16}
        cl_alri = {1: 0.7, 2: 0.1, 3: 0.07, 4: 0.07, 5: 0.06}
        cl_lc = {1: 0.2, 2: 0.1, 3: 0.24, 4: 0.23, 5: 0.23}
        cl_ihd = {1: 0.2, 2: 0.1, 3: 0.24, 4: 0.23, 5: 0.23}

        i = 1
        mort_U_vector = []
        mort_R_vector = []
        while i < 6:
            mortality_alri_U = cl_alri[i] * social_specs_file["VSL"] * mort_alri_U / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            mortality_copd_U = cl_copd[i] * social_specs_file["VSL"] * mort_copd_U / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            mortality_lc_U = cl_lc[i] * social_specs_file["VSL"] * mort_lc_U / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            mortality_ihd_U = cl_ihd[i] * social_specs_file["VSL"] * mort_ihd_U / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)

            mort_U_total = (1 + social_specs_file["Health_spillovers_parameter"]) * (
                    mortality_alri_U + mortality_copd_U + mortality_lc_U + mortality_ihd_U)

            mort_U_vector.append(mort_U_total)

            mortality_alri_R = cl_alri[i] * social_specs_file["VSL"] * mort_alri_R / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            mortality_copd_R = cl_copd[i] * social_specs_file["VSL"] * mort_copd_R / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            mortality_lc_R = cl_lc[i] * social_specs_file["VLS"] * mort_lc_R / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            mortality_ihd_R = cl_ihd[i] * social_specs_file["VSL"] * mort_ihd_R / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)

            mort_R_total = (1 + social_specs_file["Health_spillovers_parameter"]) * (
                    mortality_alri_R + mortality_copd_R + mortality_lc_R + mortality_ihd_R)

            mort_R_vector.append(mort_R_total)

        mortality_U = np.sum(mort_R_vector)
        mortality_R = np.sum(mort_R_vector)

        self.urban_mortality = mortality_U
        self.rural_mortality = mortality_R

    def morbidity(self, social_specs_file, paf_0_alri, paf_0_copd, paf_0_lc, paf_0_ihd):
        """
        Calculates morbidity rate per fuel

        Returns
        ----------
        Monetary morbidity for each stove in urban and rural settings
        """

        rr_alri, rr_copd, rr_ihd, rr_lc = self.relative_risk()

        paf_alri = self.paf(rr_alri, sfu)
        paf_copd = self.paf(rr_copd, sfu)
        paf_ihd = self.paf(rr_ihd, sfu)
        paf_lc = self.paf(rr_lc, sfu)

        morb_alri_U = social_specs_file["Urban_Hhsize"] * (paf_0_alri - paf_alri) * social_specs_file["Morb_ALRI"]
        morb_copd_U = social_specs_file["Urban_Hhsize"] * (paf_0_copd - paf_copd) * social_specs_file["Morb_COPD"]
        morb_ihd_U = social_specs_file["Urban_Hhsize"] * (paf_0_ihd - paf_ihd) * social_specs_file["Morb_IHD"]
        morb_lc_U = social_specs_file["Urban_Hhsize"] * (paf_0_lc - paf_lc) * social_specs_file["Morb_LC"]

        morb_alri_R = social_specs_file["Rural_Hhsize"] * (paf_0_alri - paf_alri) * social_specs_file["Morb_ALRI"]
        morb_copd_R = social_specs_file["Rural_Hhsize"] * (paf_0_copd - paf_copd) * social_specs_file["Morb_COPD"]
        morb_ihd_R = social_specs_file["Rural_Hhsize"] * (paf_0_ihd - paf_ihd) * social_specs_file["Morb_IHD"]
        morb_lc_R = social_specs_file["Rural_Hhsize"] * (paf_0_lc - paf_lc) * social_specs_file["Morb_LC"]

        cl_copd = {1: 0.3, 2: 0.2, 3: 0.17, 4: 0.17, 5: 0.16}
        cl_alri = {1: 0.7, 2: 0.1, 3: 0.07, 4: 0.07, 5: 0.06}
        cl_lc = {1: 0.2, 2: 0.1, 3: 0.24, 4: 0.23, 5: 0.23}
        cl_ihd = {1: 0.2, 2: 0.1, 3: 0.24, 4: 0.23, 5: 0.23}

        i = 1
        morb_U_vector = []
        morb_R_vector = []
        while i < 6:
            morbidity_alri_U = cl_alri[i] * social_specs_file["COI_ALRI"] * morb_alri_U / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            morbidity_copd_U = cl_copd[i] * social_specs_file["COI_COPD"] * morb_copd_U / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            morbidity_lc_U = cl_lc[i] * social_specs_file["COI_LC"] * morb_lc_U / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            morbidity_ihd_U = cl_ihd[i] * social_specs_file["COI_IHD"] * morb_ihd_U / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)

            morb_U_total = (1 + social_specs_file["Health_spillovers_parameter"]) * (
                    morbidity_alri_U + morbidity_copd_U + morbidity_lc_U + morbidity_ihd_U)

            morb_U_vector.append(morb_U_total)

            morbidity_alri_R = cl_alri[i] * social_specs_file["COI_ALRI"] * morb_alri_R / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            morbidity_copd_R = cl_copd[i] * social_specs_file["COI_COPD"] * morb_copd_R / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            morbidity_lc_R = cl_lc[i] * social_specs_file["COI_LC"] * morb_lc_R / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)
            morbidity_ihd_R = cl_ihd[i] * social_specs_file["COI_IHD"] * morb_ihd_R / (
                    1 + social_specs_file["Discount_rate"]) ** (i - 1)

            morb_R_total = (1 + social_specs_file["Health_spillovers_parameter"]) * (
                    morbidity_alri_R + morbidity_copd_R + morbidity_lc_R + morbidity_ihd_R)

            morb_R_vector.append(morb_R_total)

        morbidity_U = np.sum(morb_U_vector)
        morbidity_R = np.sum(morb_R_vector)

        self.urban_morbidity = morbidity_U
        self.rural_morbidity = morbidity_R


def time_save(tech, value_of_time, walking_friction, forest):
    if tech.name == 'biogas':
        time_of_collection = 2
    elif tech.name == 'traditional_biomass' or tech.name == 'improved_biomass':
        time_of_collection = 2 * (raster.travel_time(walking_friction,
                                                     forest)) + 2.2  # 2.2 hrs Medium scenario for Jeiland paper globally, placeholder
    else:
        time_of_collection = 0

    time = time_of_collection + tech.time_of_cooking
    time_value = time * value_of_time

    return time_value


def carbon_emissions(tech):
    carb = 5 * (3.64 / tech.efficiency) / tech.energy_content * (
            tech.carbon_intensity * tech.energy_content / tech.efficiency)  # 5 USD/MT is average social cost of carbon emissions in Nepal according to https://www.nature.com/articles/s41558-018-0282-y.pdf, 3.64 MJ to cook based on https://iopscience.iop.org/article/10.1088/1748-9326/aa6fd0/meta

    return carb


def discounted_meals(meals_per_year, discount_rate_tech, tech):
    discount_rate, proj_life = discount_factor(discount_rate_tech, tech)

    energy = meals_per_year * 3.64 / tech.efficiency

    energy_needed = energy * np.ones(proj_life)

    if proj_life > 1:
        energy_needed[0] = 0

    discounted_energy = energy_needed / discount_rate

    return discounted_energy


def discounted_inv(discount_rate_tech, tech):
    discount_rate, proj_life = discount_factor(discount_rate_tech, tech)

    investments = np.zeros(project_life)
    investments[0] = tech.inv_cost

    if proj_life > tech.tech_life:
        investments[tech.tech_life] = tech.inv_cost

    discounted_investments = investments / discount_rate

    return discounted_investments


def discounted_om(discount_rate_tech, tech):
    discount_rate, proj_life = discount_factor(discount_rate_tech, tech)

    operation_and_maintenance = tech.om_costs * np.ones(project_life)

    if proj_life > 1:
        operation_and_maintenance[0] = 0

        if proj_life > tech.tech_life:
            operation_and_maintenance[tech.tech_life] = 0

    discounted_om_cost = operation_and_maintenance / discount_rate

    return discounted_om_cost


def salvage(discount_rate_tech, tech):
    discount_rate, proj_life = discount_factor(discount_rate_tech, tech)

    salvage = np.zeros(project_life)
    used_life = project_life

    if proj_life > tech.tech_life:
        used_life = project_life - tech.tech_life

    salvage[-1] = tech.inv_cost * (1 - used_life / tech.tech_life)

    discounted_salvage = salvage / discount_rate

    return discounted_salvage


def discounted_fuel_cost(discount_rate_tech, tech, road_friction, lpg, meals_per_year):
    discount_rate, proj_life = discount_factor(discount_rate_tech, tech)

    if tech.name == 'electricity' or tech.name == 'improved_biomass_purchased' or tech.name == 'purchased_traditional_biomass':
        fuel_cost = (tech.fuel_cost * discounted_meals(meals_per_year, discount_rate_tech, tech)) * np.ones(
            project_life) / tech.efficiency
    elif tech.name == 'lpg':
        fuel_cost = (tech.fuel_cost * discounted_meals(meals_per_year, discount_rate_tech,
                                                       tech)) * raster.lpg_transportation_cost(
            raster.travel_time(road_friction, lpg)) / tech.efficiency
    else:
        fuel_cost = 0

    fuel_cost_discounted = fuel_cost / discount_rate

    return fuel_cost_discounted


def cost(discount_rate_tech, tech, meals_per_year, road_friction, lpg):
    cost = (discounted_inv(discount_rate_tech, tech) + discounted_om(discount_rate_tech, tech) + \
            discounted_fuel_cost(discount_rate_tech, tech, road_friction, lpg) - salvage(discount_rate_tech, tech)) / \
           discounted_meals(meals_per_year, discount_rate_tech, tech)

    return cost


def benefit(start_year, end_year, tech, discount_rate_social, hhsize_R, hhsize_U, vsl, value_of_time, walking_friction,
            forest, sfu=1):
    benefit = morbidity(start_year, end_year, tech, discount_rate_social, hhsize_R, hhsize_U, sfu) + \
              mortality(start_year, end_year, tech, discount_rate_social, hhsize_R, hhsize_U, vsl, sfu) + \
              time_save(tech, value_of_time, walking_friction, forest) + carbon_emissions(tech)

    return benefit


def net_costs(discount_rate_tech, tech, meals_per_year, road_friction, lpg, start_year, end_year, discount_rate_social,
              hhsize_R, hhsize_U, vsl, value_of_time, walking_friction, forest, sfu=1):
    net_costs = cost(discount_rate_tech, tech, meals_per_year, road_friction, lpg) - \
                benefit(start_year, end_year, tech, discount_rate_social, hhsize_R, hhsize_U, vsl, value_of_time,
                        walking_friction, forest, sfu)

    return net_costs


class LPG(Technology):
    """
    LPG technology class. Inherits all functionality from the standard
    Technology class
    """

    def __init__(self,
                 name=None,
                 carbon_intensity=0,
                 energy_content=0,
                 tech_life=0,  # in years
                 inv_cost=0,  # in USD
                 infra_cost=0,  # cost of additional infrastructure
                 fuel_cost=0,
                 time_of_cooking=0,
                 om_cost=0,  # percentage of investement cost
                 efficiency=0,  # ratio
                 pm25=0,
                 travel_time=None,
                 truck_capacity=2000,
                 diesel_price=0.88,
                 diesel_per_hour=14):
        super().__init__(name, carbon_intensity, energy_content, tech_life,
                         inv_cost, infra_cost, fuel_cost, time_of_cooking,
                         om_cost, efficiency, pm25)
        self.travel_time = travel_time
        self.truck_capacity = truck_capacity
        self.diesel_price = diesel_price
        self.diesel_per_hour = diesel_per_hour
        self.transport_cost = None

    def transportation_cost(self):
        """The cost of transporting LPG. See https://iopscience.iop.org/article/10.1088/1748-9326/6/3/034002/pdf for the formula

        Transportation cost = (2 * diesel consumption per h * national diesel price * travel time)/transported LPG

        Total cost = (LPG cost + Transportation cost)/efficiency of LPG stoves


        Each truck is assumed to transport 2,000 kg LPG
        (3.5 MT truck https://www.wlpga.org/wp-content/uploads/2019/09/2019-Guide-to-Good-Industry-Practices-for-LPG-Cylinders-in-the-
        Distribution-Channel.pdf)
        National diesel price in Nepal is assumed to be 0.88 USD/l
        Diesel consumption per h is assumed to be 14 l/h (14 l/100km)
        (https://www.iea.org/reports/fuel-consumption-of-cars-and-vans)
        LPG cost in Nepal is assumed to be 19 USD per cylinder (1.34 USD/kg)
        LPG stove efficiency is assumed to be 60%

        :param param1:  travel_time_raster
                        Hour to travel between each point and the startpoints as array
        :returns:       The cost of LPG in each cell per kg
        """
        transport_cost = (2 * self.diesel_per_hour * self.diesel_price * self.travel_time.layer) / self.truck_capacity
        self.transport_cost = transport_cost


class Biomass(Technology):
    """
    LPG technology class. Inherits all functionality from the standard
    Technology class
    """

    def __init__(self,
                 name=None,
                 carbon_intensity=0,
                 energy_content=0,
                 tech_life=0,  # in years
                 inv_cost=0,  # in USD
                 infra_cost=0,  # cost of additional infrastructure
                 fuel_cost=0,
                 time_of_cooking=0,
                 om_cost=0,  # percentage of investement cost
                 efficiency=0,  # ratio
                 pm25=0,
                 travel_time=None):
        super().__init__(name, carbon_intensity, energy_content, tech_life,
                         inv_cost, infra_cost, fuel_cost, time_of_cooking,
                         om_cost, efficiency, pm25)
        self.travel_time = travel_time
