import sys
from decouple import config
import os
sys.path.append(config('ONSSTOVE'))

import numpy as np

from onsstove.onsstove import OnSSTOVE

# 1. Read the OnSSTOVE model
country = snakemake.params.country
print(f'[{country}] Reading model')
model = OnSSTOVE.read_model(snakemake.input.model)

# 2. Read the scenario data
print(f'[{country}] Scenario data')
path = snakemake.input.scenario_file
model.read_scenario_data(path, delimiter=',')
model.output_directory = snakemake.params.output_directory
model.techs['Electricity'].get_capacity_cost(model)

# 3. Calculating benefits and costs of each technology and getting the max benefit technology for each cell
model.run(technologies=['Electricity', 'LPG', 'Biogas',
                        'Collected_Improved_Biomass', 'Collected_Traditional_Biomass', 'Charcoal ICS',
                        'Traditional_Charcoal'
                        ])

# 5. Saving data to raster files
# cmap = {"ICS": '#57365A', "LPG": '#6987B7', "Traditional biomass": '#673139', "Charcoal": '#B6195E',
#         "Biogas": '#3BE2C5', "Biogas and ICS": "#F6029E",
#         "Biogas and LPG": "#C021C0",  "Biogas and Traditional biomass": "#266AA6",
#         "Biogas and Charcoal": "#3B05DF", "Biogas and Electricity": "#484673",
#         "Electricity": '#D0DF53', "Electricity and ICS": "#4D7126",
#         "Electricity and LPG": "#004D40", "Electricity and Traditional biomass": "#FFC107",
#         "Electricity and Charcoal": "#1E88E5", "Electricity and Biogas": "#484673"}
cmap = {"Biomass ICS": '#6F4070', "LPG": '#66C5CC', "Traditional Biomass": '#994E95',
        "Traditional Charcoal": '#666666', "Charcoal ICS": '#444444',
        "Biogas": '#73AF48', "Biogas and Biomass ICS": "#F6029E",
        "Biogas and LPG": "#f97b72",  "Biogas and Traditional Biomass": "#266AA6",
        "Biogas and Traditional Charcoal": "#3B05DF",
        "Biogas and Charcoal ICS": "#3B59DF",
        "Biogas and Electricity": "#484673",
        "Electricity": '#CC503E', "Electricity and Biomass ICS": "#B497E7",
        "Electricity and LPG": "#E17C05", "Electricity and Traditional Biomass": "#FFC107",
        "Electricity and Charcoal ICS": "#660000",
        "Electricity and Biogas": "#0F8554",
        "Electricity and Traditional Charcoal": "#000000"}

labels = {"Biogas and Electricity": "Electricity and Biogas",
          'Collected Traditional Biomass': 'Traditional biomass',
          'Collected Improved Biomass': 'Biomass ICS'}

print(f'[{country}] Saving the rasters')
model.gdf['max_benefit_tech'] = model.gdf['max_benefit_tech'].str.replace('_', ' ')
model.gdf['max_benefit_tech'] = model.gdf['max_benefit_tech'].str.replace('Collected Traditional Biomass', 'Traditional biomass')
model.gdf['max_benefit_tech'] = model.gdf['max_benefit_tech'].str.replace('Collected Improved Biomass', 'Biomass ICS')
model.to_raster('max_benefit_tech', labels=labels, cmap=cmap)
model.to_raster('net_benefit_Electricity')
model.to_raster('net_benefit_LPG')
#model.to_raster('net_benefit_Collected_Traditional_Biomass')
#model.to_raster('net_benefit_Collected_Improved_Biomass')
model.to_raster('maximum_net_benefit')
model.to_raster('investment_costs')

print(f'[{country}] Saving the graphs')
model.to_image('maximum_net_benefit', cmap='Spectral', cumulative_count=[0.01, 0.99],
               title=f'Maximum net benefit | {country}', dpi=300,
               rasterized=True)
model.to_image('max_benefit_tech', cmap=cmap, legend_position=(1, 0.75),
               type='pdf', dpi=300, stats=True, stats_position=(1, 0.8),
               labels=labels, legend=True, legend_title='Maximum benefit\ncooking technology', rasterized=True)

model.plot_split(cmap=cmap, labels=labels, save=True, height=1.5, width=3.5)
model.plot_costs_benefits(labels=labels, save=True, height=1.5, width=2)
model.plot_benefit_distribution(type='box', groupby='None', cmap=cmap, labels=labels, save=True, height=1.5, width=3.5)
model.plot_benefit_distribution(type='box', groupby='IsUrban', cmap=cmap, labels=labels, save=True, height=1.5, width=3.5)
model.plot_benefit_distribution(type='box', groupby='UrbanRural', cmap=cmap, labels=labels, save=True, height=2.5, width=3.5)
model.plot_benefit_distribution(type='density', cmap=cmap, labels=labels, save=True, height=1.5, width=3.5)

print(f'[{country}] Saving the results')

model.summary().to_csv(os.path.join(snakemake.params.output_directory, 'summary.csv'), index=False)
model.to_pickle('results.pkl')

