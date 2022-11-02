import os

from onstove import OnStove

def test_plot_maps():
    # 1. Reading results
    country = 'Rwanda'
    results = OnStove.read_model(os.path.join('onstove', 'tests', 'output', 
                                              'results.pkl'))
                                              
    # 2. Crating result maps
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
              
    scale = int(results.base_layer.meta['width']//100*10000*2)
    scale_bar_prop = dict(size=scale, style='double', textprops=dict(size=8),
                          linekw=dict(lw=1, color='black'), extent=0.01)
    north_arow_prop = dict(size=30, location=(0.92, 0.92), linewidth=0.5)
              
    results.to_image('max_benefit_tech', cmap=cmap, legend_position=(1, 0.6), 
                     figsize=(7, 5), type='pdf', dpi=300, stats=True, 
                     stats_position=(1, 0.9), stats_fontsize=10, labels=labels, 
                     legend=True, 
                     legend_title='Maximum benefit\ncooking technology', 
                     legend_prop={'title': {'size': 10, 'weight': 'bold'}, 
                                  'size': 10},
                     title=f'Maximum benefit technology | {country}',
                     scale_bar=scale_bar_prop, north_arrow=north_arow_prop, 
                     rasterized=True)
    results.to_image('maximum_net_benefit', cmap='Spectral', 
                     cumulative_count=[0.01, 0.99], figsize=(7, 5),
                     title=f'Maximum net benefit | {country}', dpi=300,
                     rasterized=True, type='pdf')
    assert True