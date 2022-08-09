import sys, os
import geopandas as gpd
import pandas as pd
from decouple import config

onstove_path = config('ONSTOVE').format(os.getlogin())
sys.path.append(onstove_path)

from onstove.layer import VectorLayer
from onstove.onstove import OnStove

cmap = {"Biomass ICS (ND)": '#6F4070', "LPG": '#66C5CC', "Biomass": '#FFB6C1',
        "Biomass ICS (FD)": '#af04b3', "Pellets ICS (FD)": '#ef02f5',
        "Charcoal": '#364135', "Charcoal ICS": '#d4bdc5',
        "Biogas": '#73AF48', "Biogas and Biomass ICS (ND)": "#F6029E",
        "Biogas and Biomass ICS (FD)": "#F6029E",
        "Biogas and Pellets ICS (FD)": "#F6029E",
        "Biogas and LPG": "#0F8554", "Biogas and Biomass": "#266AA6",
        "Biogas and Charcoal": "#3B05DF",
        "Biogas and Charcoal ICS": "#3B59DF",
        "Electricity": '#CC503E', "Electricity and Biomass ICS (ND)": "#B497E7",
        "Electricity and Biomass ICS (FD)": "#B497E7",
        "Electricity and Pellets ICS (FD)": "#B497E7",
        "Electricity and LPG": "#E17C05", "Electricity and Biomass": "#FFC107",
        "Electricity and Charcoal ICS": "#660000",
        "Electricity and Biogas": "#f97b72",
        "Electricity and Charcoal": "#FF0000"}

labels = {"Biogas and Electricity": "Electricity and Biogas",
          'Collected Traditional Biomass': 'Biomass',
          'Collected Improved Biomass': 'Biomass ICS (ND)',
          'Traditional Charcoal': 'Charcoal',
          'Biomass Forced Draft': 'Biomass ICS (FD)',
          'Pellets Forced Draft': 'Pellets ICS (FD)'}

df = pd.DataFrame({'country': [], 'Households': [], 'Calibrated_pop': [],
                   'costs_Electricity': [], 'costs_LPG': [], 'costs_Biogas': [],
                   'costs_Collected_Improved_Biomass': [], 'costs_Collected_Traditional_Biomass': [],
                   'costs_Charcoal ICS': [], 'costs_Traditional_Charcoal': [],
                   'costs_Biomass Forced Draft': [], 'costs_Pellets Forced Draft': [],
                   'max_benefit_tech': [], 'maximum_net_benefit': [], 'deaths_avoided': [],
                   'health_costs_avoided': [], 'time_saved': [], 'reduced_emissions': [],
                   'investment_costs': [], 'om_costs': [], 'fuel_costs': [],
                   'emissions_costs_saved': [], 'opportunity_cost_gained': [],
                   'salvage_value': [], 'IsUrban': [], 'Current_elec': [], 'geometry': []})

print('Creating Africa model...')
africa = OnStove()
africa.output_directory = snakemake.params.output_directory

mask_layer = VectorLayer('admin', 'adm_1', path=snakemake.input.boundaries)
mask_layer.data = mask_layer.data.to_crs(3857)
africa.mask_layer = mask_layer
africa.gdf = gpd.GeoDataFrame(df, crs='epsg:3857')

print('Reading country results')
for file, country in zip(snakemake.input.results, snakemake.params.countries):
    print(f'    - {country}')
    model = OnStove.read_model(file)

    model.gdf['country'] = country
    africa.gdf = africa.gdf.append(model.gdf[df.columns], ignore_index=True)

print('Creating index...')
index = {str(g): i for i, g in enumerate(africa.gdf['geometry'].unique())}
africa.gdf['index'] = [index[str(i)] for i in africa.gdf['geometry']]

print('Saving graphs...')
africa.plot_split(cmap=cmap, labels=labels, save=True, height=1.5, width=3.5)
africa.plot_costs_benefits(labels=labels, save=True, height=1.5, width=2)
africa.plot_benefit_distribution(type='box', groupby='None', cmap=cmap,
                                 labels=labels, save=True, height=1.5, width=3.5)

print('Creating map...')
africa.to_image('max_benefit_tech', cmap=cmap, legend_position=(0.03, 0.47),
                type='pdf', dpi=300, stats=True, stats_position=(-0.002, 0.5), stats_fontsize=10,
                labels=labels, legend=True, legend_title='Maximum benefit\ncooking technology',
                rasterized=True)

print('Saving results...')
africa.summary().to_csv(os.path.join(africa.output_directory, 'summary.csv'), index=False)
africa.to_pickle('results.pkl')
