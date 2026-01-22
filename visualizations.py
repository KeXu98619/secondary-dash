import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
import json
import numpy as np
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Color schemes for different components
COLOR_SCHEMES = {
    'demand': 'Blues',
    'infrastructure': 'Greens',
    'accessibility': 'Reds',
    'equity': 'Purples',
    'composite': 'GnBu'
}


# ============================================================================
# MAP VISUALIZATION FUNCTIONS
# ============================================================================

def create_choropleth_map(gdf, column, title, colorscale='Viridis'):
    """
    Create a choropleth map with enhanced hover information.
    
    Args:
        gdf: GeoDataFrame with data
        column: Column to visualize
        title: Map title
        colorscale: Color scheme
    
    Returns:
        Plotly figure
    """
    import plotly.express as px
    
    if gdf is None or len(gdf) == 0:
        return create_empty_figure("No data to display")
    
    # Filter to feasible sites only
    display_gdf = gdf[gdf['feasible'] == True].copy()
    
    if len(display_gdf) == 0:
        return create_empty_figure("No feasible sites to display")
    
    # Ensure CRS
    if display_gdf.crs is None:
        display_gdf.set_crs('EPSG:4326', inplace=True)
    
    # Define which columns to show in hover based on the score type
    # Default hover data (always show these)
    hover_data_dict = {
        column: ':.1f',  # The main score column
        'GEOID': True,
        'composite_score': ':.1f'
    }
    
    # Add component-specific metrics
    if column == 'demand_score':
        # Demand-specific hover info
        hover_data_dict.update({
            'total_vehicles_domiciled': ':.0f' if 'total_vehicles_domiciled' in display_gdf.columns else False,
            'hdt_vehicles_domiciled': ':.0f' if 'hdt_vehicles_domiciled' in display_gdf.columns else False,
            'mdt_vehicles_domiciled': ':.0f' if 'mdt_vehicles_domiciled' in display_gdf.columns else False,
            'Heavy_Duty': ':.0f' if 'Heavy_Duty' in display_gdf.columns else False,
            'unique_heavy_trucks_daily': ':.0f' if 'unique_heavy_trucks_daily' in display_gdf.columns else (':.0f' if 'total_daily_heavy_trucks' in display_gdf.columns else False),
            'heavy_duty_demand_uniformity': ':.1f' if 'heavy_duty_demand_uniformity' in display_gdf.columns else False,
            'avg_stop_duration_minutes': ':.1f' if 'avg_stop_duration_minutes' in display_gdf.columns else False
        })
        
        custom_labels = {
            column: 'Demand Score',
            'composite_score': 'Composite Score',
            'total_vehicles_domiciled': 'Total Domiciled Vehicles',
            'hdt_vehicles_domiciled': 'Heavy-Duty Domiciled',
            'mdt_vehicles_domiciled': 'Medium-Duty Domiciled',
            'Heavy_Duty': 'Heavy-Duty Trips',
            'unique_heavy_trucks_daily': 'Unique Heavy Trucks/Day',
            'heavy_duty_demand_uniformity': 'Demand Uniformity',
            'avg_stop_duration_minutes': 'Avg Stop Duration (min)'
        }
    
    elif column == 'infrastructure_score':
        # Infrastructure-specific hover info
        hover_data_dict.update({
            'warehouses_within_5mi': True if 'warehouses_within_5mi' in display_gdf.columns else False,
            'retail_commercial_in_tract': ':.0f' if 'retail_commercial_in_tract' in display_gdf.columns else False,
            'rest_stops_within_5mi': ':.0f' if 'rest_stops_within_5mi' in display_gdf.columns else False,
            'estimated_park_ride_area_acres': ':.1f' if 'estimated_park_ride_area_acres' in display_gdf.columns else False,
            'park_ride_spaces_within_5mi': ':.0f' if 'park_ride_spaces_within_5mi' in display_gdf.columns else False,
            'intermodal_rail_facilities_within_5mi': ':.1f' if 'intermodal_rail_facilities_within_5mi' in display_gdf.columns else False,
            'ev_infrastructure_readiness': ':.1f' if 'ev_infrastructure_readiness' in display_gdf.columns else False,
            'electric_grid_suitability': ':.2f' if 'electric_grid_suitability' in display_gdf.columns else False,
            'solar_total_capacity_kw': ':.0f' if 'solar_total_capacity_kw' in display_gdf.columns else False,
            
            # NEW: E3 Substation Data (in-tract)
            'quantity_substations': ':.0f' if 'quantity_substations' in display_gdf.columns else False,
            'substations_per_sq_mi': ':.2f' if 'substations_per_sq_mi' in display_gdf.columns else False,
            'has_substation_access': True if 'has_substation_access' in display_gdf.columns else False,
            'median_feeder_headroom_mva': ':.1f' if 'median_feeder_headroom_mva' in display_gdf.columns else False,
            'grid_capacity_score': ':.1f' if 'grid_capacity_score' in display_gdf.columns else False,
            
            # NEW: National Grid Data (5mi radius)
            'substations_within_5mi': ':.0f' if 'substations_within_5mi' in display_gdf.columns else False,
            'grid_available_capacity_MVA': ':.1f' if 'grid_available_capacity_MVA' in display_gdf.columns else False,
            'ng_grid_capacity_score': ':.1f' if 'ng_grid_capacity_score' in display_gdf.columns else False,
            'grid_renewable_capacity_MW': ':.1f' if 'grid_renewable_capacity_MW' in display_gdf.columns else False,
            'grid_avg_utilization_pct': ':.1f' if 'grid_avg_utilization_pct' in display_gdf.columns else False,
            'strong_grid_access': True if 'strong_grid_access' in display_gdf.columns else False,
        })
        
        custom_labels = {
            column: 'Infrastructure Score',
            'composite_score': 'Composite Score',
            'warehouses_within_5mi': 'Warehouses (5mi)',
            'retail_commercial_in_tract': 'Retail/Commercial (in tract)',
            'rest_stops_within_5mi': 'Rest Stops (5mi)',
            'estimated_park_ride_area_acres': 'Expansion Area (acres)',
            'park_ride_spaces_within_5mi': 'Park & Ride Spaces (5mi)',
            'intermodal_rail_facilities_within_5mi': 'Intermodal Facilities (5mi)',
            'ev_infrastructure_readiness': 'EV Readiness Score',
            'electric_grid_suitability': 'Grid Suitability',
            'solar_total_capacity_kw': 'Solar Potential (kW)',
            
            # NEW: E3 labels
            'quantity_substations': 'Substations in Tract',
            'substations_per_sq_mi': 'Substation Density (per sq mi)',
            'has_substation_access': 'Has Substation',
            'median_feeder_headroom_mva': 'Feeder Headroom (MVA)',
            'grid_capacity_score': 'E3 Grid Score',
            
            # NEW: National Grid labels
            'substations_within_5mi': 'Substations Nearby (5mi)',
            'grid_available_capacity_MVA': 'Available Capacity (MVA)',
            'ng_grid_capacity_score': 'NG Grid Score',
            'grid_renewable_capacity_MW': 'Renewable Capacity (MW)',
            'grid_avg_utilization_pct': 'Avg Grid Utilization %',
            'strong_grid_access': 'Strong Grid Access (2+)',
        }
    
    elif column == 'accessibility_score':
        # Accessibility-specific hover info
        hover_data_dict.update({
            'has_interstate': True if 'has_interstate' in display_gdf.columns else False,
            'has_nhs_route': True if 'has_nhs_route' in display_gdf.columns else False,
            'total_road_miles': ':.1f' if 'total_road_miles' in display_gdf.columns else False,
            'total_lane_miles': ':.1f' if 'total_lane_miles' in display_gdf.columns else False,
            'D3AAO': ':.2f' if 'D3AAO' in display_gdf.columns else False
        })
        
        custom_labels = {
            column: 'Accessibility Score',
            'composite_score': 'Composite Score',
            'has_interstate': 'Has Interstate',
            'has_nhs_route': 'Has NHS Route',
            'total_road_miles': 'Total Road Miles',
            'total_lane_miles': 'Total Lane Miles',
            'D3AAO': 'Network Density (mi/sq mi)'
        }
    
    elif column == 'equity_feasibility_score':
        # Equity & Environmental-specific hover info
        hover_data_dict.update({
            'ej_priority_score': ':.1f' if 'ej_priority_score' in display_gdf.columns else False,
            'pct_ej_block_groups': ':.1f' if 'pct_ej_block_groups' in display_gdf.columns else False,
            'truck_suitability_final': ':.1f' if 'truck_suitability_final' in display_gdf.columns else False,
            'landuse_pct_commercial': ':.1f' if 'landuse_pct_commercial' in display_gdf.columns else False,
            'landuse_pct_industrial': ':.1f' if 'landuse_pct_industrial' in display_gdf.columns else False
        })
        
        custom_labels = {
            column: 'Equity & Environmental Score',
            'composite_score': 'Composite Score',
            'ej_priority_score': 'EJ Priority Score',
            'pct_ej_block_groups': '% EJ Block Groups',
            'truck_suitability_final': 'Truck Suitability',
            'landuse_pct_commercial': '% Commercial',
            'landuse_pct_industrial': '% Industrial'
        }
    
    else:
        custom_labels = {column: title}
    
    # Remove False values from hover_data_dict (columns that don't exist)
    hover_data_dict = {k: v for k, v in hover_data_dict.items() if v is not False}
    
    # Create choropleth
    fig = px.choropleth_mapbox(
        display_gdf,
        geojson=display_gdf.geometry.__geo_interface__,
        locations=display_gdf.index,
        color=column,
        color_continuous_scale=colorscale,
        hover_name='GEOID',
        hover_data=hover_data_dict,
        labels=custom_labels,
        mapbox_style="carto-positron",
        center={"lat": display_gdf.geometry.centroid.y.mean(),
                "lon": display_gdf.geometry.centroid.x.mean()},
        zoom=8,
        opacity=0.6,
        range_color=[display_gdf[column].min(), display_gdf[column].max()]
    )
    
    fig.update_layout(
        title=title,
        height=600,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        coloraxis_colorbar=dict(
            title=title.split()[0]  # First word of title
        )
    )
    
    return fig


def create_optimal_sites_map(scored_gdf: gpd.GeoDataFrame,
                             selected_gdf: gpd.GeoDataFrame) -> go.Figure:
    """Create comprehensive map showing scored tracts with optimal sites"""
    if scored_gdf is None or len(scored_gdf) == 0:
        return create_empty_figure("Run analysis to view results")

    try:
        # Ensure CRS is WGS84
        if scored_gdf.crs is not None and scored_gdf.crs != 'EPSG:4326':
            scored_gdf = scored_gdf.to_crs('EPSG:4326')
        if selected_gdf is not None and selected_gdf.crs is not None and selected_gdf.crs != 'EPSG:4326':
            selected_gdf = selected_gdf.to_crs('EPSG:4326')

        geojson_all = json.loads(scored_gdf.to_json())

        # Default viewport: show the full state (Massachusetts).
        # We keep a stable default center/zoom so the map doesn't start
        # overly zoomed-in (e.g., when only a subset of data is present).
        center_lat = 42.4072
        center_lon = -71.3824

        fig = go.Figure()

        # Background: All scored tracts
        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson_all,
            locations=scored_gdf.index,
            z=scored_gdf['composite_score'],
            colorscale=COLOR_SCHEMES['composite'],
            marker_opacity=0.6,
            marker_line_width=0.3,
            marker_line_color='rgba(255,255,255,0.5)',
            colorbar=dict(
                title='Score',
                thickness=12,
                len=0.6,
                x=1.0
            ),
            name='All Tracts',
            hovertemplate=(
                '<b>Tract: %{customdata[0]}</b><br>' +
                'Score: %{z:.2f}<br>' +
                '<extra></extra>'
            ),
            customdata=scored_gdf[['GEOID']].values if 'GEOID' in scored_gdf.columns
            else np.arange(len(scored_gdf)).reshape(-1, 1),
            featureidkey="id"
        ))

        # Foreground: Selected optimal sites
        if selected_gdf is not None and len(selected_gdf) > 0:
            centroids = selected_gdf.geometry.centroid

            # Add star markers for selected sites
            fig.add_trace(go.Scattermapbox(
                lat=centroids.y,
                lon=centroids.x,
                mode='markers+text',
                marker=dict(
                    size=24,
                    color='#FFD700',  # Gold
                    symbol='star',
                ),
                text=[f"#{i + 1}" for i in range(len(selected_gdf))],
                textposition="middle center",
                textfont=dict(size=10, color='#1a1a1a', family='Arial Black'),
                name='Optimal Sites',
                hovertemplate=(
                    '<b>Site #%{text}</b><br>' +
                    'GEOID: %{customdata[0]}<br>' +
                    'Score: %{customdata[1]:.2f}<br>' +
                    'Demand: %{customdata[2]:.2f}<br>' +
                    'Infrastructure: %{customdata[3]:.2f}<br>' +
                    '<extra></extra>'
                ),
                customdata=selected_gdf[[
                    'GEOID' if 'GEOID' in selected_gdf.columns else selected_gdf.index.name or 'index',
                    'composite_score',
                    'demand_score',
                    'infrastructure_score'
                ]].values
            ))

            # Add larger background circles
            fig.add_trace(go.Scattermapbox(
                lat=centroids.y,
                lon=centroids.x,
                mode='markers',
                marker=dict(
                    size=40,
                    color='rgba(255, 215, 0, 0.3)',
                    symbol='circle'
                ),
                showlegend=False,
                hoverinfo='skip'
            ))

        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                zoom=6.5,
                center={"lat": center_lat, "lon": center_lon}
            ),
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
            title=dict(
                text="Optimal Truck Charging Sites - Massachusetts",
                font=dict(size=18, color="#2c3e50", family="Arial Black"),
                x=0.5,
                xanchor='center'
            ),
            height=700,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="gray",
                borderwidth=1
            ),
            paper_bgcolor='white'
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating optimal sites map: {e}", exc_info=True)
        return create_empty_figure(f"Error: {str(e)}")


def create_initial_map() -> go.Figure:
    """Create initial empty map showing Massachusetts"""
    fig = go.Figure(go.Scattermapbox(
        lat=[42.4072],
        lon=[-71.3824],
        mode='text',
        text=[''],
        showlegend=False,
        hoverinfo='skip'
    ))

    fig.update_layout(
        mapbox={
            'style': "carto-positron",
            'center': {'lat': 42.4072, 'lon': -71.3824},
            'zoom': 6.5
        },
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        title={
            'text': "Massachusetts Truck Charging Site Selection",
            'font': {'size': 18, 'color': "#2c3e50", 'family': "Arial Black"},
            'x': 0.5,
            'xanchor': 'center'
        },
        height=700,
        paper_bgcolor='white',
        annotations=[{
            'text': "Click 'Run Analysis' to begin site selection",
            'xref': "paper",
            'yref': "paper",
            'x': 0.5,
            'y': 0.5,
            'showarrow': False,
            'font': {'size': 16, 'color': "#7f8c8d"},
            'bgcolor': "rgba(255,255,255,0.9)",
            'bordercolor': "#bdc3c7",
            'borderwidth': 2,
            'borderpad': 10
        }]
    )

    return fig


def create_empty_figure(message: str) -> go.Figure:
    """Create an empty figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray")
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=400
    )
    return fig


# ============================================================================
# CHART VISUALIZATION FUNCTIONS
# ============================================================================

def create_score_distribution_chart(scored_gdf: gpd.GeoDataFrame) -> go.Figure:
    """Create distribution histogram with statistics overlay"""
    if scored_gdf is None or 'composite_score' not in scored_gdf.columns:
        return create_empty_figure("No score data available")

    scores = scored_gdf['composite_score'].dropna()
    scores = scores[scores > 0]  # Filter out infeasible sites

    if len(scores) == 0:
        return create_empty_figure("No feasible sites found")

    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=40,
        marker=dict(
            color='steelblue',
            line=dict(color='white', width=1)
        ),
        name='Distribution',
        hovertemplate='Score Range: %{x}<br>Count: %{y}<extra></extra>'
    ))

    # Add mean line
    mean_score = scores.mean()
    fig.add_vline(
        x=mean_score,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_score:.2f}",
        annotation_position="top right"
    )

    # Add median line
    median_score = scores.median()
    fig.add_vline(
        x=median_score,
        line_dash="dot",
        line_color="green",
        annotation_text=f"Median: {median_score:.2f}",
        annotation_position="top left"
    )

    fig.update_layout(
        title="Distribution of Composite Scores (Feasible Tracts Only)",
        xaxis_title="Composite Score",
        yaxis_title="Number of Tracts",
        height=400,
        showlegend=False,
        paper_bgcolor='white',
        plot_bgcolor='rgba(240,240,240,0.5)',
        font=dict(family="Arial", size=12)
    )

    return fig


def create_component_comparison_chart(scored_gdf: gpd.GeoDataFrame,
                                      top_n: int = 20) -> go.Figure:
    """Create grouped bar chart comparing component scores"""
    if scored_gdf is None:
        return create_empty_figure("No data available")

    # Filter to feasible sites
    feasible_scores = scored_gdf[scored_gdf['feasible'] == True]

    if len(feasible_scores) == 0:
        return create_empty_figure("No feasible sites found")

    top_tracts = feasible_scores.nlargest(min(top_n, len(feasible_scores)), 'composite_score')

    # Create tract labels
    tract_labels = [
        f"...{str(geoid)[-4:]}" if 'GEOID' in top_tracts.columns
        else f"Tract {i + 1}"
        for i, geoid in enumerate(top_tracts['GEOID'] if 'GEOID' in top_tracts.columns
                                  else range(len(top_tracts)))
    ]

    fig = go.Figure()

    components = [
        ('demand_score', 'Demand', '#3498db'),
        ('infrastructure_score', 'Infrastructure', '#2ecc71'),
        ('accessibility_score', 'Accessibility', '#e74c3c'),
        ('equity_feasibility_score', 'Equity/Feasibility', '#9b59b6')
    ]

    for col, name, color in components:
        if col in top_tracts.columns:
            fig.add_trace(go.Bar(
                name=name,
                x=tract_labels,
                y=top_tracts[col],
                marker_color=color,
                hovertemplate=f'{name}: %{{y:.2f}}<extra></extra>'
            ))

    fig.update_layout(
        title=f"Component Score Breakdown - Top {len(top_tracts)} Tracts",
        barmode='group',
        height=450,
        xaxis=dict(
            title="Census Tract",
            tickangle=-45,
            tickfont=dict(size=10)
        ),
        yaxis=dict(title="Score", range=[0, 100]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        paper_bgcolor='white',
        plot_bgcolor='rgba(240,240,240,0.5)',
        font=dict(family="Arial", size=12)
    )

    return fig


def create_radar_chart(selected_sites: gpd.GeoDataFrame) -> go.Figure:
    """Create radar chart comparing selected sites"""
    if selected_sites is None or len(selected_sites) == 0:
        return create_empty_figure("No sites selected")

    categories = ['Demand', 'Infrastructure', 'Accessibility', 'Equity']

    fig = go.Figure()

    for idx, row in selected_sites.iterrows():
        values = [
            row.get('demand_score', 0),
            row.get('infrastructure_score', 0),
            row.get('accessibility_score', 0),
            row.get('equity_feasibility_score', 0)
        ]

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],  # Close the polygon
            theta=categories + [categories[0]],
            fill='toself',
            name=f'Site {idx + 1}',
            hovertemplate='%{theta}: %{r:.2f}<extra></extra>'
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        title="Component Score Comparison - Selected Sites",
        height=450,
        showlegend=True,
        paper_bgcolor='white'
    )

    return fig


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_score_color(score: float) -> str:
    """Return color based on score value for Bootstrap badges/progress bars"""
    if score < 25:
        return "danger"
    elif score < 50:
        return "warning"
    elif score < 75:
        return "info"
    else:
        return "success"
        
       
        
def add_truck_chargers_to_map(fig, truck_chargers_gdf):
    """
    Add truck charging stations as markers to an existing map figure.
    
    Args:
        fig: Plotly figure object
        truck_chargers_gdf: GeoDataFrame with truck charger locations
    
    Returns:
        Updated figure with truck charger markers
    """
    import plotly.graph_objects as go
    
    if truck_chargers_gdf is None or len(truck_chargers_gdf) == 0:
        return fig
    
    # Create hover text
    hover_text = []
    for idx, row in truck_chargers_gdf.iterrows():
        text = f"<b>{row.get('name', 'Truck Charger')}</b><br>"
        text += f"{row.get('address', '')}<br>"
        text += f"{row.get('city', '')}, {row.get('state', '')} {row.get('zip', '')}<br>"
        
        if pd.notna(row.get('level2_ports')) and row.get('level2_ports', 0) > 0:
            text += f"Level 2: {int(row['level2_ports'])} ports<br>"
        if pd.notna(row.get('dcfc_ports')) and row.get('dcfc_ports', 0) > 0:
            text += f"DC Fast: {int(row['dcfc_ports'])} ports<br>"
        
        if pd.notna(row.get('hours')):
            text += f"Hours: {row['hours']}<br>"
        if pd.notna(row.get('pricing')):
            text += f"Pricing: {row['pricing']}"
        
        hover_text.append(text)
    
    # Add as scatter markers
    fig.add_trace(go.Scattermapbox(
        lat=truck_chargers_gdf['lat'],
        lon=truck_chargers_gdf['lon'],
        mode='markers',
        marker=dict(
            size=12,
            color='purple',
            symbol='charging-station',  # or 'circle'
            line=dict(width=2, color='white')
        ),
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        name='Existing Truck Chargers',
        showlegend=True
    ))
    
    return fig