import dash
from dash import Input, Output, State, dcc, ALL, Patch
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html
import geopandas as gpd
import pandas as pd
import json
import logging
from data_loader import get_selector
from visualizations import (
    create_optimal_sites_map,
    create_empty_figure,
    create_initial_map,
    create_score_distribution_chart,
    create_component_comparison_chart,
    create_radar_chart,
    get_score_color
)

# Setup logging
logger = logging.getLogger(__name__)


def register_callbacks(app):
    """Register all Dash callbacks"""

    # ========================================================================
    # NAVIGATION CALLBACKS
    # ========================================================================

    @app.callback(
        Output('outer-tabs', 'active_tab'),
        [Input('go-to-analysis-btn', 'n_clicks')],
        [State('outer-tabs', 'active_tab')]
    )
    def go_to_analysis(n_clicks, current_tab):
        """Navigate to analysis dashboard"""
        if n_clicks is None:
            raise PreventUpdate
        return "tab-analysis"
    
    
    #@app.callback(
    #    Output('outer-tabs', 'active_tab', allow_duplicate=True),
    #   [Input('outer-tabs', 'id')],
    #    prevent_initial_call='initial_duplicate'
    #)
    #def set_initial_tab(_):
    #    """
    #    Automatically open Analysis Dashboard on page load.
    #    Users who want to see Home page can click the Home tab.
    #    """
    #    return "tab-analysis"

    # ========================================================================
    # SUB-WEIGHT EXPAND/COLLAPSE CALLBACKS
    # ========================================================================

    @app.callback(
        [Output('demand-subweights-collapse', 'is_open'),
         Output('demand-expand-btn', 'children')],
        [Input('demand-expand-btn', 'n_clicks')],
        [State('demand-subweights-collapse', 'is_open')]
    )
    def toggle_demand_subweights(n_clicks, is_open):
        """Toggle demand sub-weights section"""
        if n_clicks is None:
            raise PreventUpdate
        
        new_state = not is_open
        icon = html.I(className="fas fa-chevron-up" if new_state else "fas fa-chevron-down")
        return new_state, icon

    @app.callback(
        [Output('infrastructure-subweights-collapse', 'is_open'),
         Output('infrastructure-expand-btn', 'children')],
        [Input('infrastructure-expand-btn', 'n_clicks')],
        [State('infrastructure-subweights-collapse', 'is_open')]
    )
    def toggle_infrastructure_subweights(n_clicks, is_open):
        """Toggle infrastructure sub-weights section"""
        if n_clicks is None:
            raise PreventUpdate
        
        new_state = not is_open
        icon = html.I(className="fas fa-chevron-up" if new_state else "fas fa-chevron-down")
        return new_state, icon

    @app.callback(
        [Output('accessibility-subweights-collapse', 'is_open'),
         Output('accessibility-expand-btn', 'children')],
        [Input('accessibility-expand-btn', 'n_clicks')],
        [State('accessibility-subweights-collapse', 'is_open')]
    )
    def toggle_accessibility_subweights(n_clicks, is_open):
        """Toggle accessibility sub-weights section"""
        if n_clicks is None:
            raise PreventUpdate
        
        new_state = not is_open
        icon = html.I(className="fas fa-chevron-up" if new_state else "fas fa-chevron-down")
        return new_state, icon

    @app.callback(
        [Output('equity-subweights-collapse', 'is_open'),
         Output('equity-expand-btn', 'children')],
        [Input('equity-expand-btn', 'n_clicks')],
        [State('equity-subweights-collapse', 'is_open')]
    )
    def toggle_equity_subweights(n_clicks, is_open):
        """Toggle equity sub-weights section"""
        if n_clicks is None:
            raise PreventUpdate
        
        new_state = not is_open
        icon = html.I(className="fas fa-chevron-up" if new_state else "fas fa-chevron-down")
        return new_state, icon

    # ========================================================================
    # WEIGHT SLIDER CALLBACKS
    # ========================================================================

    @app.callback(
        [Output(f'{category}-badge', 'children') for category in
         ['demand', 'infrastructure', 'accessibility', 'equity']],
        [Input(f'{category}-weight', 'value') for category in
         ['demand', 'infrastructure', 'accessibility', 'equity']]
    )
    def update_weight_badges(*weights):
        """Update weight percentage badges"""
        return [f"{w}%" for w in weights]

    @app.callback(
        Output('weight-validation', 'children'),
        [Input(f'{category}-weight', 'value') for category in
         ['demand', 'infrastructure', 'accessibility', 'equity']]
    )
    def validate_weights(demand, infra, access, equity):
        """Validate that weights sum to 100%"""
        total = sum([demand, infra, access, equity])

        # Use tolerance to avoid float/rounding artifacts (e.g., 99.999999 -> displays as 100)
        if abs(total - 100) < 0.01:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Total: {total:.0f}% ✓"
            ], color="success", className="py-2 px-3 mb-0 small")
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Total: {total:.0f}% (should be 100%)"
            ], color="warning", className="py-2 px-3 mb-0 small")

    # ========================================================================
    # SUB-WEIGHT VALIDATION CALLBACKS
    # ========================================================================

    @app.callback(
        Output('infrastructure-subweight-validation', 'children'),
        [Input('ev-gap-subweight', 'value'),
         Input('park-ride-subweight', 'value'),
         Input('government-subweight', 'value')]
    )
    def validate_infrastructure_subweights(ev_gap, park_ride, government):
        """Validate that infrastructure sub-weights sum to 100"""
        if any(v is None for v in [ev_gap, park_ride, government]):
            raise PreventUpdate

        total = ev_gap + park_ride + government

        if abs(total - 100) < 0.5:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-1"),
                f"Sum: {total:.0f} ✓"
            ], color="success", className="py-1 px-2 mb-0 small")
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-1"),
                f"Sum: {total:.0f} (should be 100)"
            ], color="warning", className="py-1 px-2 mb-0 small")

    @app.callback(
        Output('accessibility-subweight-validation', 'children'),
        [Input('network-density-subweight', 'value'),
         Input('grocery-subweight', 'value'),
         Input('gas-station-subweight', 'value')]
    )
    def validate_accessibility_subweights(network, grocery, gas_station):
        """Validate that accessibility sub-weights sum to 100"""
        if any(v is None for v in [network, grocery, gas_station]):
            raise PreventUpdate

        total = network + grocery + gas_station

        if abs(total - 100) < 0.5:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-1"),
                f"Sum: {total:.0f} ✓"
            ], color="success", className="py-1 px-2 mb-0 small")
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-1"),
                f"Sum: {total:.0f} (should be 100)"
            ], color="warning", className="py-1 px-2 mb-0 small")


    @app.callback(
        Output('equity-subweight-validation', 'children'),
        [Input('ej-priority-subweight', 'value'),
         Input('landuse-suit-subweight', 'value'),
         Input('commercial-subweight', 'value'),
         Input('protected-penalty-subweight', 'value')]
    )
    def validate_equity_subweights(ej, landuse, commercial, protected):
        """Validate that equity sub-weights sum appropriately"""
        if any(v is None for v in [ej, landuse, commercial, protected]):
            raise PreventUpdate
        
        positive_sum = ej + landuse + commercial

        # In the UI, subweights are "points" that should sum to 100.
        # For Equity & Feasibility we expect: (ej + landuse + commercial) = 90, penalty = 10.
        if abs(positive_sum - 90) < 0.5 and abs(protected - 10) < 0.5:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-1"),
                f"Positive weights: {positive_sum:.0f} ✓, Penalty: {protected:.0f}"
            ], color="success", className="py-1 px-2 mb-0 small")
        else:
            return dbc.Alert([
                html.I(className="fas fa-info-circle me-1"),
                f"Positive: {positive_sum:.0f}, Penalty: {protected:.0f} (target: 90 / 10)"
            ], color="info", className="py-1 px-2 mb-0 small")

    # ========================================================================
    # RESET SUB-WEIGHTS CALLBACKS
    # ========================================================================

    @app.callback(
        [Output('home-end-subweight', 'value'),
         Output('workplace-end-subweight', 'value'),
         Output('other-end-subweight', 'value'),
         Output('weekday-subweight', 'value'),
         Output('weekend-subweight', 'value'),
         Output('equity-community-subweight', 'value'),
         Output('non-equity-community-subweight', 'value'),
         Output('temporal-stability-subweight', 'value'),
         Output('temporal-peak-subweight', 'value')],
        [Input('reset-demand-subweights-btn', 'n_clicks')]
    )
    def reset_demand_subweights(n_clicks):
        # Reset demand sub-weights to defaults
        if n_clicks is None:
            raise PreventUpdate
        # All subweights are expressed as 0–100 "points" and should sum to 100
        # within each subfactor group.
        return (
            40, 40, 20,   # Trip purpose
            70, 30,       # Day of week
            50, 50,       # Equity vs non-equity
            60, 40        # Temporal pattern
        )

    @app.callback(
        [Output('ev-gap-subweight', 'value'),
         Output('park-ride-subweight', 'value'),
         Output('government-subweight', 'value')],
        [Input('reset-infrastructure-subweights-btn', 'n_clicks')]
    )
    def reset_infrastructure_subweights(n_clicks):
        """Reset infrastructure sub-weights to defaults"""
        if n_clicks is None:
            raise PreventUpdate
        return (45, 30, 25)


    @app.callback(
        [Output('network-density-subweight', 'value'),
         Output('grocery-subweight', 'value'),
         Output('gas-station-subweight', 'value')],
        [Input('reset-accessibility-subweights-btn', 'n_clicks')]
    )
    def reset_accessibility_subweights(n_clicks):
        """Reset accessibility sub-weights to defaults"""
        if n_clicks is None:
            raise PreventUpdate
        return (50, 25, 25)


    @app.callback(
        [Output('ej-priority-subweight', 'value'),
         Output('landuse-suit-subweight', 'value'),
         Output('commercial-subweight', 'value'),
         Output('protected-penalty-subweight', 'value')],
        [Input('reset-equity-subweights-btn', 'n_clicks')]
    )
    def reset_equity_subweights(n_clicks):
        """Reset equity sub-weights to defaults"""
        if n_clicks is None:
            raise PreventUpdate
        # Positive weights should sum to 90; penalty should be 10.
        return (40, 35, 15, 10)

    # ========================================================================
    # MAIN ANALYSIS CALLBACK
    # ========================================================================

    @app.callback(
        [Output('scored-data-store', 'data'),
         Output('selected-sites-store', 'data'),
         Output('summary-metrics', 'children')],
        [Input('run-analysis-btn', 'n_clicks')],
        # Main category weights
        [State(f'{cat}-weight', 'value') for cat in
         ['demand', 'infrastructure', 'accessibility', 'equity']] +
        
        # DEMAND sub-weights
        [State('home-end-subweight', 'value'),
         State('workplace-end-subweight', 'value'),
         State('other-end-subweight', 'value'),
         State('weekday-subweight', 'value'),
         State('weekend-subweight', 'value'),
         State('equity-community-subweight', 'value'),
         State('non-equity-community-subweight', 'value'),
         State('temporal-stability-subweight', 'value'),
         State('temporal-peak-subweight', 'value')] +

        # INFRASTRUCTURE sub-weights
        [State('ev-gap-subweight', 'value'),
         State('park-ride-subweight', 'value'),
         State('government-subweight', 'value')] +

        
        # ACCESSIBILITY sub-weights
        [State('network-density-subweight', 'value'),
         State('grocery-subweight', 'value'),
         State('gas-station-subweight', 'value')] +

        
        # EQUITY sub-weights
        [State('ej-priority-subweight', 'value'),
         State('landuse-suit-subweight', 'value'),
         State('commercial-subweight', 'value'),
         State('protected-penalty-subweight', 'value')] +
        
        # Other parameters
        [State('n-sites-input', 'value'),
         State('min-person-input', 'value'),
         State('secondary-buffer-toggle', 'value'),
         State('rural-only-toggle', 'value'),
         State('exclude-zero-headroom-toggle', 'value')]
    )
    def run_analysis(n_clicks, 
                     # Main weights
                     demand_w, infra_w, access_w, equity_w,
                     # Demand sub-weights
                     home_end_w, workplace_end_w, other_end_w,
                     weekday_w, weekend_w,
                     equity_community_w, non_equity_community_w,
                     temporal_stability_w, temporal_peak_w,
                     # Infrastructure sub-weights
                     ev_gap_w, park_ride_w, government_w,
                     # Accessibility sub-weights
                     network_density_w, grocery_w, gas_station_w,
                     # Equity sub-weights
                     ej_priority_w, landuse_suit_w, commercial_w, protected_penalty_w,
                     # Other params
                     n_sites, min_person_trips, secondary_buffer_value, rural_only_value,
                     exclude_zero_headroom_value):
        """Execute site selection analysis"""
        if n_clicks is None:
            raise PreventUpdate

        try:
            # Validate main weights
            total_weight = demand_w + infra_w + access_w + equity_w
            if total_weight != 100:
                logger.warning(f"Weights sum to {total_weight}%, normalizing...")
                factor = 100 / total_weight
                demand_w *= factor
                infra_w *= factor
                access_w *= factor
                equity_w *= factor

            # Get the cached selector
            selector = get_selector()

            # Update main category weights
            selector.config['weights'] = {
                'demand': demand_w / 100,
                'infrastructure': infra_w / 100,
                'accessibility': access_w / 100,
                'equity_feasibility': equity_w / 100
            }
            
            # ===== NEW: Update all sub-weights =====
            
            # Demand sub-weights
            selector.config['demand_weights'] = {
                # Trip purpose
                'home_end_weight': home_end_w,
                'workplace_end_weight': workplace_end_w,
                'other_end_weight': other_end_w,

                # Day of week
                'weekday_weight': weekday_w,
                'weekend_weight': weekend_w,

                # Equity vs non-equity trips
                'equity_community_weight': equity_community_w,
                'non_equity_community_weight': non_equity_community_w,

                # Temporal pattern
                'temporal_stability_weight': temporal_stability_w,
                'temporal_peak_weight': temporal_peak_w
            }

            # Demand component weights (fixed design share; normalized in selector)
            selector.config['demand_component_weights'] = {
                'purpose': 0.35,
                'day_of_week': 0.25,
                'equity_trips': 0.20,
                'temporal_pattern': 0.20
            }

            # Infrastructure sub-weights
            infra_sub_sum = ev_gap_w + park_ride_w + government_w

            if infra_sub_sum > 0:
                selector.config['infrastructure_weights'] = {
                    'truck_charger_gap_weight': (ev_gap_w / infra_sub_sum),
                    'park_ride_weight': (park_ride_w / infra_sub_sum),
                    'government_weight': (government_w / infra_sub_sum)
                }
            else:
                # Treat all-zeros as "disable this section"
                selector.config['infrastructure_weights'] = {
                    'truck_charger_gap_weight': 0.0,
                    'park_ride_weight': 0.0,
                    'government_weight': 0.0
                }

            
            # Accessibility sub-weights
            access_sub_sum = network_density_w + grocery_w + gas_station_w
            if access_sub_sum > 0:
                selector.config['accessibility_weights'] = {
                    'network_weight': network_density_w / access_sub_sum,
                    'grocery_weight': grocery_w / access_sub_sum,
                    'gas_station_weight': gas_station_w / access_sub_sum
                }
            else:
                # Treat all-zeros as "disable this section"
                selector.config['accessibility_weights'] = {
                    'network_weight': 0.0,
                    'grocery_weight': 0.0,
                    'gas_station_weight': 0.0
                }

            
            # Equity sub-weights
            equity_sub_sum = ej_priority_w + landuse_suit_w + commercial_w + protected_penalty_w
            if equity_sub_sum > 0:
                selector.config['equity_weights'] = {
                    'ej_priority_weight': ej_priority_w / equity_sub_sum,
                    'landuse_suit_weight': landuse_suit_w / equity_sub_sum,
                    'tier_bonus_weight': commercial_w / equity_sub_sum,
                    'protected_penalty_weight': protected_penalty_w / equity_sub_sum
                }
            else:
                # Treat all-zeros as "disable this section"
                selector.config['equity_weights'] = {
                    'ej_priority_weight': 0.0,
                    'landuse_suit_weight': 0.0,
                    'tier_bonus_weight': 0.0,
                    'protected_penalty_weight': 0.0
                }
            
            # ===== END sub-weights update =====

            # Update feasibility constraints
            selector.config['constraints']['min_person_trips'] = min_person_trips

            # NEW: Optional buffer constraint (checklist value is [] when off, ['within'] when on)
            selector.config['constraints']['only_within_secondary_buffer'] = bool(secondary_buffer_value)


            # Optional: only keep rural tracts
            selector.config['constraints']['only_rural'] = bool(rural_only_value)
            # Optional: remove tracts with 0 feeder headroom from feasible sites
            selector.config['constraints']['exclude_zero_headroom'] = bool(exclude_zero_headroom_value)

            # Log the equity weights being used
            logger.info(f"Equity weights applied: {selector.config['equity_weights']}")

            # Run scoring with updated configuration
            logger.info("Calculating composite scores...")
            scored_data = selector.calculate_composite_score()

            # Select optimal sites
            logger.info(f"Selecting {n_sites} optimal sites...")
            optimal_sites = selector.select_optimal_sites(
                n_sites=int(n_sites),
                min_distance_mi=0
            )

            # Create summary metrics (unchanged)
            feasible_count = len(scored_data[scored_data['feasible'] == True])
            avg_score = scored_data[scored_data['feasible'] == True]['composite_score'].mean()

            from layout import create_metric_card

            metrics = dbc.Row([
                dbc.Col([
                    create_metric_card(
                        "Total Tracts Analyzed",
                        str(len(scored_data)),
                        "fas fa-map",
                        "info"
                    )
                ], md=3),
                dbc.Col([
                    create_metric_card(
                        "Feasible Sites",
                        str(feasible_count),
                        "fas fa-check-circle",
                        "success"
                    )
                ], md=3),
                dbc.Col([
                    create_metric_card(
                        "Sites Selected",
                        str(len(optimal_sites)),
                        "fas fa-star",
                        "warning"
                    )
                ], md=3),
                dbc.Col([
                    create_metric_card(
                        "Avg Composite Score",
                        f"{avg_score:.1f}",
                        "fas fa-chart-line",
                        "primary"
                    )
                ], md=3)
            ])

            # Convert to JSON
            def gdf_to_json(gdf):
                try:
                    return json.dumps(gdf.__geo_interface__)
                except:
                    data_dict = gdf.drop(columns='geometry').to_dict('records')
                    geoms = [geom.__geo_interface__ for geom in gdf.geometry]
                    return json.dumps({
                        'type': 'FeatureCollection',
                        'features': [
                            {'type': 'Feature', 'properties': props, 'geometry': geom}
                            for props, geom in zip(data_dict, geoms)
                        ]
                    })

            scored_json = gdf_to_json(scored_data)
            optimal_json = gdf_to_json(optimal_sites)

            logger.info("Analysis completed successfully")
            return (scored_json, optimal_json, metrics)

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            error_alert = dbc.Alert([
                html.H5("Analysis Failed", className="alert-heading"),
                html.P(f"Error: {str(e)}"),
                html.Hr(),
                html.P("Check the console for detailed error information.",
                       className="mb-0 small")
            ], color="danger", className="m-3")
            return None, None, error_alert

    # ========================================================================
    # MAP UPDATE CALLBACKS
    # ========================================================================

    @app.callback(
        Output('overview-map', 'figure'),
        [Input('scored-data-store', 'data'),
         Input('selected-sites-store', 'data'),
         Input({'type': 'tract-link', 'index': ALL}, 'n_clicks')],
        [State({'type': 'tract-link', 'index': ALL}, 'id'),
         State('overview-map', 'figure')]
    )
    def update_overview_map(scored_json, optimal_json, tract_link_clicks, tract_link_ids, current_fig):
        """Update the main overview map.

        Performance/UX notes:
        - When the user clicks a tract GEOID link, we *only* patch the map viewport
          (center/zoom) to avoid re-creating traces and triggering a full re-render.
        - When new analysis results are produced, we redraw the full figure.
        """
        if scored_json is None or optimal_json is None:
            return create_initial_map()

        try:
            # Parse JSON back to GeoDataFrame
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            optimal_gdf = gpd.GeoDataFrame.from_features(json.loads(optimal_json))

            # Set CRS if not present
            if scored_gdf.crs is None:
                scored_gdf.set_crs('EPSG:4326', inplace=True)
            if optimal_gdf.crs is None:
                optimal_gdf.set_crs('EPSG:4326', inplace=True)

            # Identify what triggered this callback
            try:
                triggered_id = dash.callback_context.triggered_id
            except Exception:
                triggered_id = None

            # If a tract GEOID link was clicked, patch only the viewport for a smooth zoom.
            if isinstance(triggered_id, dict) and triggered_id.get('type') == 'tract-link':
                clicked_geoid = triggered_id.get('index')
                if clicked_geoid is not None and 'GEOID' in scored_gdf.columns:
                    subset = scored_gdf[scored_gdf['GEOID'].astype(str) == str(clicked_geoid)]
                    if len(subset) > 0 and current_fig is not None:
                        centroid = subset.geometry.iloc[0].centroid
                        patch = Patch()
                        patch['layout']['mapbox']['center'] = {
                            'lat': float(centroid.y),
                            'lon': float(centroid.x)
                        }
                        patch['layout']['mapbox']['zoom'] = 11
                        return patch

            # Otherwise (new analysis results, refresh, etc.), redraw the whole map.
            fig = create_optimal_sites_map(scored_gdf, optimal_gdf)
            return fig
        except Exception as e:
            logger.error(f"Error updating overview map: {e}", exc_info=True)
            return create_initial_map()

        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            
            # Set CRS if not present
            if scored_gdf.crs is None:
                scored_gdf.set_crs('EPSG:4326', inplace=True)

            return (
                create_choropleth_map(scored_gdf, 'demand_score',
                                      'Demand Score', COLOR_SCHEMES['demand']),
                create_choropleth_map(scored_gdf, 'infrastructure_score',
                                      'Infrastructure Score', COLOR_SCHEMES['infrastructure']),
                create_choropleth_map(scored_gdf, 'accessibility_score',
                                      'Accessibility Score', COLOR_SCHEMES['accessibility']),
                create_choropleth_map(scored_gdf, 'equity_feasibility_score',
                                      'Equity & Environmental Score', COLOR_SCHEMES['equity'])
            )
        except Exception as e:
            logger.error(f"Error updating component maps: {e}", exc_info=True)
            empty = create_empty_figure(f"Error: {str(e)}")
            return empty, empty, empty, empty

    # ========================================================================
    # SITE RANKINGS TABLE CALLBACK
    # ========================================================================

    @app.callback(
        Output('site-rankings-table', 'children'),
        [Input('selected-sites-store', 'data')]
    )
    def update_site_rankings(optimal_json):
        """Create detailed rankings table for selected sites WITH CHARGING TYPE"""
        if optimal_json is None:
            return html.P("Run analysis to see selected sites",
                          className="text-muted text-center")

        try:
            optimal_gdf = gpd.GeoDataFrame.from_features(json.loads(optimal_json))

            if len(optimal_gdf) == 0:
                return html.P("No sites selected", className="text-muted text-center")

            # Define charging type display formatting
            type_icons = {
                'depot_overnight': ('🏭', 'Depot/Overnight', 'primary'),
                'opportunistic_topup': ('⚡', 'Opportunistic', 'warning'),
                'en_route_corridor': ('🛣️', 'En-Route/Corridor', 'success'),
                'mixed': ('🔀', 'Mixed', 'info'),
                'none': ('❓', 'Unclassified', 'secondary')
            }

            # Create table rows
            rows = []
            for idx, row in optimal_gdf.iterrows():
                ctype = row.get('charging_type', 'none')
                icon, type_label, badge_color = type_icons.get(ctype, ('', 'Unclassified', 'secondary'))
                
                rows.append(
                    html.Tr([
                        html.Td(
                            dbc.Badge(f"#{idx + 1}", color="dark"),
                            className="text-center"
                        ),
                        html.Td(
                            html.A(
                                row.get('GEOID', f'Tract {idx}'),
                                href="#",
                                id={'type': 'tract-link', 'index': str(row.get('GEOID', f'{idx}'))},
                                n_clicks=0,
                                className="font-monospace small"
                            )
                        ),
                        html.Td([
                            html.Span(icon, className="me-1"),
                            dbc.Badge(type_label, color=badge_color, className="me-2"),
                        ], className="text-nowrap"),
                        html.Td(
                            dbc.Progress(
                                value=row['composite_score'],
                                label=f"{row['composite_score']:.1f}",
                                color=get_score_color(row['composite_score']),
                                className="mb-0",
                                style={"height": "25px"}
                            )
                        ),
                        
                        # # Add a column for context
                        # html.Td([
                            # html.Span(
                                # "🏙️" if row.get('urban_rural_context') == 'urban' else
                                # "🌳" if row.get('urban_rural_context') == 'rural' else
                                # "🏘️" if row.get('urban_rural_context') == 'mixed' else "❓",
                                # className="me-1"
                            # ),
                            # row.get('urban_rural_context', 'Unknown').title()
                        # ], className="small"),
                        
                        
                        html.Td(f"{row.get('demand_score', 0):.1f}",
                                className="text-center"),
                        html.Td(f"{row.get('infrastructure_score', 0):.1f}",
                                className="text-center"),
                        html.Td(f"{row.get('accessibility_score', 0):.1f}",
                                className="text-center"),
                        html.Td(f"{row.get('equity_feasibility_score', 0):.1f}",
                                className="text-center")
                    ], className="align-middle")
                )

            return dbc.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Rank", className="text-center"),
                        html.Th("Tract ID"),
                        html.Th("Charging Type", className="text-center"),
                        html.Th("Composite Score", style={"width": "20%"}),
                        html.Th("Demand", className="text-center small"),
                        html.Th("Infra", className="text-center small"),
                        html.Th("Access", className="text-center small"),
                        html.Th("Equity", className="text-center small")
                    ], className="table-primary")
                ),
                html.Tbody(rows)
            ], bordered=True, hover=True, responsive=True, striped=True,
                className="mb-0")
        except Exception as e:
            logger.error(f"Error creating rankings table: {e}", exc_info=True)
            return html.P(f"Error: {str(e)}", className="text-danger")

    # ========================================================================
    # ANALYTICS CHARTS CALLBACKS
    # ========================================================================

    @app.callback(
        [Output('score-distribution', 'figure'),
         Output('component-comparison', 'figure'),
         Output('radar-comparison', 'figure')],
        [Input('scored-data-store', 'data'),
         Input('selected-sites-store', 'data')]
    )
    def update_analytics(scored_json, optimal_json):
        """Update all analytics visualizations"""
        if scored_json is None:
            empty = create_empty_figure("Run analysis first")
            return empty, empty, empty

        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            optimal_gdf = (gpd.GeoDataFrame.from_features(json.loads(optimal_json))
                           if optimal_json else None)

            return (
                create_score_distribution_chart(scored_gdf),
                create_component_comparison_chart(scored_gdf, top_n=20),
                create_radar_chart(optimal_gdf) if optimal_gdf is not None
                else create_empty_figure("No sites selected")
            )
        except Exception as e:
            logger.error(f"Error updating analytics: {e}", exc_info=True)
            empty = create_empty_figure(f"Error: {str(e)}")
            return empty, empty, empty

    # ========================================================================
    # RESET CALLBACK
    # ========================================================================

    @app.callback(
        [Output(f'{cat}-weight', 'value') for cat in
         ['demand', 'infrastructure', 'accessibility', 'equity']] +
        [Output('n-sites-input', 'value'),
         Output('min-person-input', 'value')],
        [Input('reset-btn', 'n_clicks')]
    )
    def reset_configuration(n_clicks):
        # Reset all inputs to default values
        if n_clicks is None:
            raise PreventUpdate

        return (
            40, 25, 20, 15,  # Weights
            4,               # n_sites
            10               # min_person_trips
        )


    # ========================================================================
    # STOP DURATION CALLBACKS
    # ========================================================================

    @app.callback(
        [
            Output('avg-stop-duration', 'children'),
            Output('pct-eligible-trips', 'children')
        ],
        Input('outer-tabs', 'active_tab')  # Trigger on tab load
    )
    def update_stop_duration_metrics(_):
        """Display overall stop duration statistics"""
        selector = get_selector()
        gdf = selector.gdf
        
        avg_stop = gdf['avg_stop_duration_minutes'].mean()
        pct_eligible = gdf['pct_charging_eligible'].mean()
        
        return f"{avg_stop:.1f} min", f"{pct_eligible:.1f}%"
    
    
    @app.callback(
        Output('stop-duration-histogram', 'figure'),
        Input('outer-tabs', 'active_tab')
    )
    def create_stop_duration_histogram(_):
        """Create histogram showing distribution of average stop durations"""
        import plotly.graph_objects as go
        
        selector = get_selector()
        gdf = selector.gdf
        
        # Create histogram
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=gdf['avg_stop_duration_minutes'],
            nbinsx=30,
            name='Tracts',
            marker_color='steelblue',
            hovertemplate='Stop Duration: %{x:.0f} min<br>Count: %{y}<extra></extra>'
        ))
        
        # Add vertical line at 30-minute threshold
        fig.add_vline(
            x=30,
            line_dash="dash",
            line_color="red",
            annotation_text="Minimum Threshold (30 min)",
            annotation_position="top right"
        )
        
        # Add vertical line at 60-minute threshold
        fig.add_vline(
            x=60,
            line_dash="dot",
            line_color="orange",
            annotation_text="Ideal for DC Fast (60 min)",
            annotation_position="top"
        )
        
        fig.update_layout(
            title="Distribution of Average Stop Duration by Census Tract",
            xaxis_title="Average Stop Duration (minutes)",
            yaxis_title="Number of Census Tracts",
            hovermode='x unified',
            showlegend=False,
            height=350,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    
    @app.callback(
        Output('stop-duration-stats-table', 'children'),
        Input('outer-tabs', 'active_tab')
    )
    def create_stop_duration_stats_table(_):
        """Create summary statistics table for stop duration"""
        
        selector = get_selector()
        gdf = selector.gdf
        
        # Calculate statistics by stop duration category
        stats = []
        
        categories = [
            ("< 30 min", 0, 30, "Not viable"),
            ("30-60 min", 30, 60, "Good for Level 2"),
            ("60-120 min", 60, 120, "Ideal for DC Fast"),
            ("> 120 min", 120, 999, "Extended stops")
        ]
        
        for label, min_dur, max_dur, desc in categories:
            mask = (gdf['avg_stop_duration_minutes'] >= min_dur) & \
                   (gdf['avg_stop_duration_minutes'] < max_dur)
            
            tracts_count = mask.sum()
            trips_count = gdf.loc[mask, 'charging_eligible_trip_ends'].sum()
            pct_tracts = 100 * tracts_count / len(gdf)
            
            stats.append({
                'Duration': label,
                'Description': desc,
                'Tracts': tracts_count,
                '% of Tracts': f"{pct_tracts:.1f}%",
                'Eligible Trips': f"{trips_count:,.0f}"
            })
        
        # Create Bootstrap table
        return dbc.Table.from_dataframe(
            pd.DataFrame(stats),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        )
        
        
    @app.callback(
        Output('temporal-subweight-validation', 'children'),
        [Input('temporal-stability-subweight', 'value'),
         Input('temporal-peak-subweight', 'value')]
    )
    def validate_temporal_subweights(stability, peak):
        # Validate that temporal sub-weights sum to 100
        if any(v is None for v in [stability, peak]):
            raise PreventUpdate

        total = stability + peak

        if abs(total - 100) < 0.5:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-1"),
                f"Sum: {total:.0f} ✓"
            ], color="success", className="py-1 px-2 mb-0 small")
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-1"),
                f"Sum: {total:.0f} (should be 100)"
            ], color="warning", className="py-1 px-2 mb-0 small")


    # ========================================================================
    # TEMPORAL DEMAND PATTERN CALLBACKS
    # ========================================================================

    @app.callback(
        [
            Output('avg-demand-uniformity', 'children'),
            Output('avg-peak-intensity', 'children'),
            Output('stable-sites-count', 'children'),  # NEW
            Output('recommended-charging-breakdown', 'children')
        ],
        Input('outer-tabs', 'active_tab')
    )
    def update_temporal_metrics(_):
        """Display overall temporal demand pattern statistics"""
        selector = get_selector()
        gdf = selector.gdf
        
        # Calculate averages
        avg_uniformity = gdf['heavy_duty_demand_uniformity'].mean()
        avg_peak = gdf['heavy_duty_peak_to_avg_ratio'].mean()
        
        # Count stable sites (uniformity > 70)
        stable_count = (gdf['heavy_duty_demand_uniformity'] > 70).sum()
        
        # Charging type breakdown
        if 'truck_recommended_charging_type' in gdf.columns:
            breakdown = gdf['truck_recommended_charging_type'].value_counts()
            breakdown_html = html.Ul([
                html.Li(f"{type_}: {count} tracts ({count/len(gdf)*100:.1f}%)")
                for type_, count in breakdown.items()
            ], className="mb-0 small")
        else:
            breakdown_html = html.P("Charging type data not available", className="text-muted small")
        
        return f"{avg_uniformity:.1f}", f"{avg_peak:.2f}x", str(stable_count), breakdown_html


    @app.callback(
        Output('temporal-pattern-scatter', 'figure'),
        [Input('scored-data-store', 'data'),  # Make sure this is scored-data-store
         Input('selected-sites-store', 'data')]
    )
    def create_temporal_scatter(scored_json, optimal_json):
        """Create scatter plot of temporal stability vs peak intensity"""
        import plotly.graph_objects as go
        
        if scored_json is None:
            return create_empty_figure("Run analysis first")
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            
            # Filter to feasible sites only
            feasible = scored_gdf[scored_gdf['feasible'] == True].copy()
            
            if len(feasible) == 0:
                return create_empty_figure("No feasible sites")
            
            # Check which column name exists
            if 'heavy_duty_demand_uniformity' in feasible.columns:
                uniformity_col = 'heavy_duty_demand_uniformity'
            elif 'demand_uniformity' in feasible.columns:
                uniformity_col = 'demand_uniformity'
            else:
                # Fallback: get from selector
                selector = get_selector()
                full_data = selector.gdf[selector.gdf['GEOID'].isin(feasible['GEOID'])]
                feasible['heavy_duty_demand_uniformity'] = full_data['heavy_duty_demand_uniformity'].values
                uniformity_col = 'heavy_duty_demand_uniformity'
            
            # Check for peak ratio column
            if 'heavy_duty_peak_to_avg_ratio' in feasible.columns:
                peak_col = 'heavy_duty_peak_to_avg_ratio'
            elif 'temporal_peak_intensity' in feasible.columns:
                peak_col = 'temporal_peak_intensity'
            else:
                # Fallback: get from selector
                selector = get_selector()
                full_data = selector.gdf[selector.gdf['GEOID'].isin(feasible['GEOID'])]
                feasible['heavy_duty_peak_to_avg_ratio'] = full_data['heavy_duty_peak_to_avg_ratio'].values
                peak_col = 'heavy_duty_peak_to_avg_ratio'
            
            # Create scatter plot
            fig = go.Figure()
            
            # Add all feasible sites
            fig.add_trace(go.Scatter(
                x=feasible[uniformity_col],
                y=feasible[peak_col], 
                mode='markers',
                name='All Feasible Sites',
                marker=dict(
                    size=8,
                    color=feasible['demand_score'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Demand<br>Score"),
                    line=dict(width=1, color='white')
                ),
                text=feasible['GEOID'],
                hovertemplate=(
                    '<b>%{text}</b><br>' +
                    'Uniformity: %{x:.1f}/100<br>' +
                    'Peak Ratio: %{y:.2f}<br>' +
                    '<extra></extra>'
                )
            ))
            
            # Add selected sites if available
            if optimal_json:
                try:
                    optimal_gdf = gpd.GeoDataFrame.from_features(json.loads(optimal_json))
                    
                    # Get uniformity and peak for optimal sites
                    if uniformity_col in optimal_gdf.columns and peak_col in optimal_gdf.columns:
                        opt_uniformity = optimal_gdf[uniformity_col]
                        opt_peak = optimal_gdf[peak_col]
                    else:
                        # Get from selector
                        selector = get_selector()
                        full_data = selector.gdf[selector.gdf['GEOID'].isin(optimal_gdf['GEOID'])]
                        opt_uniformity = full_data['heavy_duty_demand_uniformity'].values
                        opt_peak = full_data['heavy_duty_peak_to_avg_ratio'].values
                    
                    fig.add_trace(go.Scatter(
                        x=opt_uniformity, 
                        y=opt_peak, 
                        mode='markers',
                        name='Selected Sites',
                        marker=dict(
                            size=15,
                            color='red',
                            symbol='star',
                            line=dict(width=2, color='yellow')
                        ),
                        text=optimal_gdf['GEOID'],
                        hovertemplate=(
                            '<b>SELECTED: %{text}</b><br>' +
                            'Uniformity: %{x:.1f}/100<br>' +
                            'Peak Ratio: %{y:.2f}<br>' +
                            '<extra></extra>'
                        )
                    ))
                except Exception as e:
                    logger.warning(f"Could not add optimal sites to scatter: {e}")
            
            # Add quadrant lines
            fig.add_hline(y=1.5, line_dash="dash", line_color="gray", opacity=0.5)
            fig.add_vline(x=70, line_dash="dash", line_color="gray", opacity=0.5)
            
            # Add annotations for quadrants
            annotations = [
                dict(x=85, y=1.2, text="Stable Demand<br>(Good for Depot)", 
                     showarrow=False, font=dict(size=10, color="green")),
                dict(x=85, y=2.5, text="Stable + Peaky<br>(Mixed Strategy)", 
                     showarrow=False, font=dict(size=10, color="orange")),
                dict(x=35, y=1.2, text="Low Activity", 
                     showarrow=False, font=dict(size=10, color="gray")),
                dict(x=35, y=2.5, text="Highly Variable<br>(Fast Charging)", 
                     showarrow=False, font=dict(size=10, color="red"))
            ]
            
            fig.update_layout(
                title="Temporal Demand Patterns: Stability vs Peak Intensity",
                xaxis_title="Demand Uniformity (0-100)<br>← Variable | Uniform →",
                yaxis_title="Peak-to-Average Ratio<br>← Low Peaks | High Peaks →",
                hovermode='closest',
                height=500,
                annotations=annotations,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating temporal scatter: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return create_empty_figure(f"Error: {str(e)}")


    @app.callback(
        Output('temporal-tod-heatmap', 'figure'),
        [Input('selected-sites-store', 'data')]
    )
    def create_temporal_tod_heatmap(optimal_json):
        """Create heatmap showing time-of-day patterns for selected sites"""
        import plotly.graph_objects as go
        
        if optimal_json is None:
            return create_empty_figure("Run analysis to see selected sites")
        
        try:
            optimal_gdf = gpd.GeoDataFrame.from_features(json.loads(optimal_json))
            selector = get_selector()
            
            if len(optimal_gdf) == 0:
                return create_empty_figure("No sites selected")
            
            # Get time-of-day columns
            tod_cols = [
                'Heavy_Duty__AM_Peak_6_10',
                'Heavy_Duty__Midday_10_15',
                'Heavy_Duty__PM_Peak_15_19',
                'Heavy_Duty__Evening_19_6'
            ]
            
            time_labels = ['AM Peak\n(6-10)', 'Midday\n(10-15)', 'PM Peak\n(15-19)', 'Evening\n(19-6)']
            
            # Get data for selected sites
            selected_geoids = optimal_gdf['GEOID'].tolist()
            tod_data = selector.gdf[selector.gdf['GEOID'].isin(selected_geoids)][['GEOID'] + tod_cols]
            
            # Normalize by row for better visualization
            tod_matrix = tod_data[tod_cols].values
            tod_normalized = tod_matrix / tod_matrix.sum(axis=1, keepdims=True) * 100
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=tod_normalized,
                x=time_labels,
                y=[f"Site #{i+1}<br>{geoid[:6]}..." for i, geoid in enumerate(tod_data['GEOID'])],
                colorscale='RdYlGn',
                text=tod_normalized,
                texttemplate='%{text:.1f}%',
                textfont={"size": 10},
                colorbar=dict(title="% of Daily<br>Trips"),
                hovertemplate=(
                    'Site: %{y}<br>' +
                    'Time: %{x}<br>' +
                    'Share: %{z:.1f}%<br>' +
                    '<extra></extra>'
                )
            ))
            
            fig.update_layout(
                title="Time-of-Day Trip Distribution for Selected Sites",
                xaxis_title="Time of Day",
                yaxis_title="Selected Sites",
                height=max(300, len(tod_data) * 50),
                margin=dict(l=150, r=50, t=80, b=50)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating TOD heatmap: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")
            
            
    @app.callback(
        Output('charging-type-suitability-chart', 'figure'),
        [Input('selected-sites-store', 'data')]
    )
    def create_suitability_comparison(optimal_json):
        """Create grouped bar chart comparing suitability scores for each selected site"""
        import plotly.graph_objects as go
        
        if optimal_json is None:
            return create_empty_figure("Run analysis to see selected sites")
        
        try:
            optimal_gdf = gpd.GeoDataFrame.from_features(json.loads(optimal_json))
            
            if len(optimal_gdf) == 0:
                return create_empty_figure("No sites selected")
            
            # Create site labels
            site_labels = [f"Site #{i+1}<br>{row['GEOID'][:8]}..." 
                           for i, (_, row) in enumerate(optimal_gdf.iterrows())]
            
            # Create traces for each suitability type
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Depot Suitability',
                x=site_labels,
                y=optimal_gdf['depot_score'],
                marker_color='#1f77b4',
                text=optimal_gdf['depot_score'].round(1),
                textposition='auto'
            ))
            
            fig.add_trace(go.Bar(
                name='Opportunistic Suitability',
                x=site_labels,
                y=optimal_gdf['opportunistic_score'],
                marker_color='#ff7f0e',
                text=optimal_gdf['opportunistic_score'].round(1),
                textposition='auto'
            ))
            
            fig.add_trace(go.Bar(
                name='Corridor Suitability',
                x=site_labels,
                y=optimal_gdf['corridor_score'],
                marker_color='#2ca02c',
                text=optimal_gdf['corridor_score'].round(1),
                textposition='auto'
            ))
            
            fig.update_layout(
                title="Charging Type Suitability Comparison - Selected Sites",
                xaxis_title="Selected Sites",
                yaxis_title="Suitability Score (0-100)",
                barmode='group',
                height=400,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating suitability comparison: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")
            
            
    # ========================================================================
    # CHARGING TYPE CALLBACKS
    # ========================================================================

    @app.callback(
        [
            Output('charging-type-depot-count', 'children'),
            Output('charging-type-opportunistic-count', 'children'),
            Output('charging-type-corridor-count', 'children'),
            Output('charging-type-mixed-count', 'children')
        ],
        Input('scored-data-store', 'data')  # ← Keep this
    )
    def update_charging_type_metrics(scored_json):  # ← CHANGE parameter name
        """Display charging type distribution statistics"""
        if scored_json is None:  # ← CHANGE variable name
            return "0", "0", "0", "0"
        
        try:
            # Parse JSON to GeoDataFrame
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))  # ← PARSE JSON
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            long_count = (feasible['charging_type'] == 'long_distance').sum()
            other_count = (feasible['charging_type'] == 'other').sum()
            
            # Keep 4-card layout; last two are placeholders
            return str(long_count), str(other_count), "0", "0"
        except Exception as e:
            logger.error(f"Error calculating charging type metrics: {e}")
            return "N/A", "N/A", "N/A", "N/A"


    @app.callback(
        Output('charging-type-breakdown-chart', 'figure'),
        [Input('scored-data-store', 'data'),
         Input('selected-sites-store', 'data')]
    )
    def create_charging_type_breakdown(scored_json, optimal_json):
        """Create pie chart showing charging type distribution"""
        import plotly.graph_objects as go
        
        if scored_json is None:
            return create_empty_figure("Run analysis first")
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            # Count by type
            type_counts = feasible['charging_type'].value_counts()
            
            # Define colors for each type
            color_map = {
                'long_distance': '#2ca02c',  # Green
                'other': '#7f7f7f'          # Gray
            }

            # Define labels
            label_map = {
                'long_distance': 'Long-distance share > 5%',
                'other': 'Other (≤ 5%)'
            }
            
            labels = [label_map.get(t, t) for t in type_counts.index]
            colors = [color_map.get(t, '#7f7f7f') for t in type_counts.index]
            
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=type_counts.values,
                marker=dict(colors=colors, line=dict(color='white', width=2)),
                textinfo='label+percent',
                textposition='auto',
                hovertemplate=(
                    '<b>%{label}</b><br>' +
                    'Sites: %{value}<br>' +
                    'Percentage: %{percent}<br>' +
                    '<extra></extra>'
                )
            )])
            
            # Add selected sites overlay if available
            if optimal_json:
                optimal_gdf = gpd.GeoDataFrame.from_features(json.loads(optimal_json))
                selected_types = optimal_gdf['charging_type'].value_counts()
                
                fig.add_annotation(
                    text=f"<b>Selected Sites ({len(optimal_gdf)}):</b><br>" + 
                         "<br>".join([f"{label_map.get(t, t)}: {c}" 
                                      for t, c in selected_types.items()]),
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    showarrow=False,
                    align="left",
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="black",
                    borderwidth=1,
                    font=dict(size=10)
                )
            
            fig.update_layout(
                title="Charging Facility Type Distribution (Feasible Sites)",
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating charging type breakdown: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")


    @app.callback(
        Output('charging-type-map', 'figure'),
        [Input('scored-data-store', 'data'),  # ← Keep this
         Input('charging-type-filter', 'value')]
    )
    def create_charging_type_map(scored_json, filter_value):  # ← Already correct!
        """Create map showing tracts colored by charging type"""
        import plotly.express as px
        
        if scored_json is None:
            return create_initial_map()
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json)) 
            
            # Filter by selected type if not 'all'
            if filter_value and filter_value != 'all':
                display_gdf = scored_gdf[scored_gdf['charging_type'] == filter_value].copy()
            else:
                # Show ALL feasible sites regardless of classification
                display_gdf = scored_gdf[scored_gdf['feasible'] == True].copy()
            
            if len(display_gdf) == 0:
                return create_empty_figure(f"No sites found for type: {filter_value}")
            
            # Define label mapping
            label_map = {
                'long_distance': 'Long-distance share > 5%',
                'other': 'Other (≤ 5%)'
            }

            
            # Add display labels - handle missing charging_type gracefully
            display_gdf['type_label'] = display_gdf['charging_type'].fillna('other').map(
                lambda x: label_map.get(x, 'Other (≤ 5%)')
            )
            
            # Define color mapping for DISPLAY LABELS
            color_discrete_map = {
                'Long-distance share > 5%': '#2ca02c',
                'Other (≤ 5%)': '#7f7f7f'
            }
            
            # Create choropleth using type_label for colors
            fig = px.choropleth_mapbox(
                display_gdf,
                geojson=display_gdf.geometry.__geo_interface__,
                locations=display_gdf.index,
                color='type_label',  # Use display label for coloring
                color_discrete_map=color_discrete_map,
                hover_name='GEOID',
                hover_data={
                    'type_label': True,
                    'composite_score': ':.1f',
                    'depot_score': ':.1f',
                    'opportunistic_score': ':.1f',
                    'corridor_score': ':.1f',
                    'charging_type': False
                },
                labels={
                    'type_label': 'Charging Type',
                    'composite_score': 'Composite Score',
                    'depot_score': 'Depot Suitability',
                    'opportunistic_score': 'Opportunistic Suitability',
                    'corridor_score': 'Corridor Suitability'
                },
                mapbox_style="carto-positron",
                center={"lat": display_gdf.geometry.centroid.y.mean(),
                        "lon": display_gdf.geometry.centroid.x.mean()},
                zoom=8,
                opacity=0.6
            )
            
            fig.update_layout(
                title=f"Charging Facility Types" + 
                      (f" - {label_map.get(filter_value, filter_value)}" if filter_value != 'all' else ""),
                height=600,
                margin={"r": 0, "t": 50, "l": 0, "b": 0},
                legend_title_text='Charging Type'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating charging type map: {e}", exc_info=True)
            return create_initial_map()


    @app.callback(
        Output('charging-type-characteristics-table', 'children'),
        Input('scored-data-store', 'data')
    )
    def create_charging_type_characteristics(scored_json):
        """Create table showing average characteristics by charging type"""
        if scored_json is None:
            return html.P("Run analysis to see characteristics", className="text-muted text-center")
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True].copy()
            
            # Calculate average metrics by type
            type_stats = []
            
            for ctype in ['depot_overnight', 'opportunistic_topup', 'en_route_corridor', 'mixed']:
                subset = feasible[feasible['charging_type'] == ctype]
                
                if len(subset) == 0:
                    continue
                
                # Check if domicile data is in scored_gdf
                if 'total_vehicles_domiciled' in scored_gdf.columns:
                    # Use data directly from scored_gdf
                    avg_domiciled = subset['total_vehicles_domiciled'].mean()
                else:
                    # Fallback: Get from selector's full data
                    selector = get_selector()
                    full_data = selector.gdf[selector.gdf['GEOID'].isin(subset['GEOID'])]
                    avg_domiciled = full_data.get('total_vehicles_domiciled', pd.Series(0)).mean()
                
                # Get other metrics - check if they exist in scored_gdf first
                if 'avg_stop_duration_minutes' in scored_gdf.columns:
                    avg_stop_dur = subset['avg_stop_duration_minutes'].mean()
                else:
                    selector = get_selector()
                    full_data = selector.gdf[selector.gdf['GEOID'].isin(subset['GEOID'])]
                    avg_stop_dur = full_data.get('avg_stop_duration_minutes', pd.Series(0)).mean()
                
                if 'unique_heavy_trucks_daily' in scored_gdf.columns:
                    avg_aadt = subset['unique_heavy_trucks_daily'].mean()
                else:
                    selector = get_selector()
                    full_data = selector.gdf[selector.gdf['GEOID'].isin(subset['GEOID'])]
                    avg_aadt = full_data.get('unique_heavy_trucks_daily', pd.Series(0)).mean()
                
                if 'heavy_duty_demand_uniformity' in scored_gdf.columns:
                    avg_uniformity = subset['heavy_duty_demand_uniformity'].mean()
                else:
                    selector = get_selector()
                    full_data = selector.gdf[selector.gdf['GEOID'].isin(subset['GEOID'])]
                    avg_uniformity = full_data.get('heavy_duty_demand_uniformity', pd.Series(0)).mean()
                
                type_stats.append({
                    'Type': ctype.replace('_', ' ').title(),
                    'Count': len(subset),
                    'Avg Score': f"{subset['composite_score'].mean():.1f}",
                    'Avg Domiciled': f"{avg_domiciled:.0f}",
                    'Avg Stop Dur.': f"{avg_stop_dur:.0f} min",
                    'Avg Unique HD Trucks/Day': f"{avg_aadt:.0f}",
                    'Avg Uniformity': f"{avg_uniformity:.0f}"
                })
            
            if not type_stats:
                return html.P("No classified sites found", className="text-muted text-center")
            
            # Create DataFrame and table
            import pandas as pd
            stats_df = pd.DataFrame(type_stats)
            
            return dbc.Table.from_dataframe(
                stats_df,
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                size='sm',
                className="mb-0"
            )
            
        except Exception as e:
            logger.error(f"Error creating characteristics table: {e}", exc_info=True)
            return html.P(f"Error: {str(e)}", className="text-danger")
            
            
    # ========================================================================
    # URBAN/RURAL CONTEXT CALLBACKS
    # ========================================================================

    @app.callback(
        [
            Output('urban-context-count', 'children'),
            Output('rural-context-count', 'children'),
            Output('mixed-context-count', 'children')
        ],
        Input('scored-data-store', 'data')  # ← Keep this
    )
    def update_urban_rural_metrics(scored_json):  # ← CHANGE parameter name
        """Display urban/rural distribution statistics"""
        if scored_json is None:  # ← CHANGE variable name
            return "0", "0", "0"
        
        try:
            # Parse JSON to GeoDataFrame
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))  # ← PARSE JSON
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            urban_count = (feasible['urban_rural_context'] == 'urban').sum()
            rural_count = (feasible['urban_rural_context'] == 'rural').sum()
            mixed_count = (feasible['urban_rural_context'] == 'mixed').sum()
            
            return str(urban_count), str(rural_count), str(mixed_count)
        except Exception as e:
            logger.error(f"Error calculating urban/rural metrics: {e}")
            return "N/A", "N/A", "N/A"


    # ========================================================================
    # URBAN/RURAL VISUALIZATIONS IN CHARGING TYPES TAB
    # ========================================================================

    @app.callback(
        Output('urban-rural-map', 'figure'),
        [Input('scored-data-store', 'data'),  # ← CHANGED from analysis-trigger
         Input('urban-rural-filter', 'value')]
    )
    def create_urban_rural_map(scored_json, filter_value):  # ← CHANGED parameter name
        """Create map showing tracts colored by urban/rural context"""
        import plotly.express as px
        
        if scored_json is None:
            return create_initial_map()
        
        try:
            # Parse JSON to GeoDataFrame
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))  # ← ADDED
            
            # Filter by selected context if not 'all'
            if filter_value and filter_value != 'all':
                display_gdf = scored_gdf[scored_gdf['urban_rural_context'] == filter_value].copy()
            else:
                display_gdf = scored_gdf[scored_gdf['feasible'] == True].copy()
            
            if len(display_gdf) == 0:
                return create_empty_figure(f"No sites found for context: {filter_value}")
            
            # Ensure CRS
            if display_gdf.crs is None:
                display_gdf.set_crs('EPSG:4326', inplace=True)
            
            # Define color mapping
            color_discrete_map = {
                'Urban': '#e74c3c',    # Red
                'Rural': '#27ae60',    # Green
                'Mixed': '#f39c12',    # Orange
                'Unknown': '#95a5a6'   # Gray
            }
            
            label_map = {
                'urban': 'Urban',
                'rural': 'Rural',
                'mixed': 'Mixed',
                'unknown': 'Unknown'
            }
            
            # Add display labels
            display_gdf['context_label'] = display_gdf['urban_rural_context'].map(
                lambda x: label_map.get(x, 'Unknown')
            )
            
            # Create choropleth
            fig = px.choropleth_mapbox(
                display_gdf,
                geojson=display_gdf.geometry.__geo_interface__,
                locations=display_gdf.index,
                color='context_label',
                color_discrete_map=color_discrete_map,
                hover_name='GEOID',
                hover_data={
                    'context_label': True,
                    'composite_score': ':.1f',
                    'urban_context_bonus': True,
                    'rural_context_bonus': True,
                    'landuse_diversity_score': ':.1f',
                    'urban_rural_context': False
                },
                labels={
                    'context_label': 'Urban/Rural Context',
                    'composite_score': 'Composite Score',
                    'urban_context_bonus': 'Urban Bonus',
                    'rural_context_bonus': 'Rural Bonus',
                    'landuse_diversity_score': 'Land Use Diversity'
                },
                mapbox_style="carto-positron",
                center={"lat": display_gdf.geometry.centroid.y.mean(),
                        "lon": display_gdf.geometry.centroid.x.mean()},
                zoom=8,
                opacity=0.6
            )
            
            fig.update_layout(
                title=f"Urban/Rural Context" + 
                      (f" - {label_map.get(filter_value, filter_value)}" if filter_value and filter_value != 'all' else ""),
                height=600,
                margin={"r": 0, "t": 50, "l": 0, "b": 0},
                legend_title_text='Context'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating urban/rural map: {e}", exc_info=True)
            return create_initial_map()


    @app.callback(
        Output('urban-rural-breakdown-chart', 'figure'),
        Input('scored-data-store', 'data')  # ← CHANGED from analysis-trigger
    )
    def create_urban_rural_breakdown(scored_json):  # ← CHANGED parameter name
        """Create pie chart showing urban/rural distribution"""
        import plotly.graph_objects as go
        
        if scored_json is None:
            return create_empty_figure("Run analysis first")
        
        try:
            # Parse JSON to GeoDataFrame
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))  # ← ADDED
            
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            # Count by context
            context_counts = feasible['urban_rural_context'].value_counts()
            
            color_map = {
                'urban': '#e74c3c',
                'rural': '#27ae60',
                'mixed': '#f39c12',
                'unknown': '#95a5a6'
            }
            
            label_map = {
                'urban': 'Urban',
                'rural': 'Rural',
                'mixed': 'Mixed',
                'unknown': 'Unknown'
            }
            
            labels = [label_map.get(c, c) for c in context_counts.index]
            colors = [color_map.get(c, '#95a5a6') for c in context_counts.index]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=context_counts.values,
                marker=dict(colors=colors, line=dict(color='white', width=2)),
                textinfo='label+percent',
                textposition='auto',
                hovertemplate=(
                    '<b>%{label}</b><br>' +
                    'Sites: %{value}<br>' +
                    'Percentage: %{percent}<br>' +
                    '<extra></extra>'
                )
            )])
            
            fig.update_layout(
                title="Urban/Rural Context Distribution (Feasible Sites)",
                height=400,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating urban/rural breakdown: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")


    @app.callback(
        Output('context-by-charging-type-chart', 'figure'),
        Input('scored-data-store', 'data')  # ← CHANGED from analysis-trigger
    )
    def create_context_by_charging_type(scored_json):  # ← CHANGED parameter name
        """Create stacked bar showing charging types by urban/rural context"""
        import plotly.graph_objects as go
        
        if scored_json is None:
            return create_empty_figure("Run analysis first")
        
        try:
            # Parse JSON to GeoDataFrame
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))  # ← ADDED
            
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            # Cross-tabulation
            crosstab = pd.crosstab(
                feasible['urban_rural_context'],
                feasible['charging_type']
            )
            
            fig = go.Figure()
            
            charging_colors = {
                'long_distance': '#2ca02c',
                'other': '#7f7f7f'
            }
            charging_labels = {
                'long_distance': 'Long-distance share > 5%',
                'other': 'Other (≤ 5%)'
            }
            
            for charging_type in crosstab.columns:
                fig.add_trace(go.Bar(
                    name=charging_labels.get(charging_type, charging_type),
                    x=crosstab.index,
                    y=crosstab[charging_type],
                    marker_color=charging_colors.get(charging_type, '#7f7f7f')
                ))
            
            fig.update_layout(
                title="Charging Types by Urban/Rural Context",
                xaxis_title="Context",
                yaxis_title="Number of Sites",
                barmode='stack',
                height=400,
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating context/charging chart: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")
            
            
    @app.callback(
        Output('truck-chargers-list', 'children'),
        Input('outer-tabs', 'active_tab')
    )
    def display_truck_chargers(_):
        """Display list of existing truck charging facilities"""
        from data_loader import get_truck_chargers
        
        truck_chargers = get_truck_chargers()
        
        if truck_chargers is None or len(truck_chargers) == 0:
            return html.P("No truck charger data available", className="text-muted small")
        
        items = []
        for idx, row in truck_chargers.iterrows():
            items.append(
                html.Li([
                    html.Strong(row.get('name', 'Unknown'), className="d-block"),
                    html.Small(f"{row.get('city', '')}, MA", className="text-muted d-block"),
                    html.Small([
                        f"L2: {int(row.get('level2_ports', 0))} ports" if pd.notna(row.get('level2_ports')) else "",
                        " | " if (pd.notna(row.get('level2_ports')) and pd.notna(row.get('dcfc_ports'))) else "",
                        f"DCFC: {int(row.get('dcfc_ports', 0))} ports" if pd.notna(row.get('dcfc_ports')) else ""
                    ], className="text-muted")
                ], className="mb-2")
            )
        
        return html.Ul(items, className="small mb-0")
        
        
        
    # Add to callbacks.py
    @app.callback(
        [
            Output('total-domiciled-vehicles', 'children'),
            Output('hdt-domiciled-avg', 'children'),
            Output('mdt-domiciled-avg', 'children'),
            Output('avg-domicile-concentration', 'children')
        ],
        Input('outer-tabs', 'active_tab')
    )
    def update_domicile_metrics(_):
        """Display domiciled vehicle statistics"""
        selector = get_selector()
        gdf = selector.gdf
        
        total_domiciled = gdf['total_vehicles_domiciled'].sum()
        hdt_avg = gdf['hdt_vehicles_domiciled'].mean()
        mdt_avg = gdf['mdt_vehicles_domiciled'].mean()
        avg_concentration = gdf['total_domiciled_concentration_score'].mean()
        
        return (
            f"{total_domiciled:,.0f}",
            f"{hdt_avg:.1f}",
            f"{mdt_avg:.1f}",
            f"{avg_concentration:.1f}"
        )


    @app.callback(
        Output('domicile-distribution-chart', 'figure'),
        Input('analysis-trigger', 'data')
    )
    def create_domicile_distribution(trigger):
        """Create chart showing domiciled vehicle distribution"""
        import plotly.graph_objects as go
        
        if trigger is None:
            return create_empty_figure("Run analysis first")
        
        try:
            from data_loader import get_scored_data
            scored_gdf = get_scored_data()
            
            if scored_gdf is None:
                return create_empty_figure("No data available")
            
            selector = get_selector()
            full_data = selector.gdf[selector.gdf['GEOID'].isin(scored_gdf['GEOID'])]
            
            # Get top 30 tracts by domiciled vehicles
            top_tracts = full_data.nlargest(30, 'total_vehicles_domiciled')
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Heavy Duty',
                x=top_tracts['GEOID'],
                y=top_tracts['hdt_vehicles_domiciled'],
                marker_color='#e74c3c'
            ))
            
            fig.add_trace(go.Bar(
                name='Medium Duty',
                x=top_tracts['GEOID'],
                y=top_tracts['mdt_vehicles_domiciled'],
                marker_color='#f39c12'
            ))
            
            fig.update_layout(
                title="Top 30 Tracts by Domiciled Vehicles (HDT + MDT)",
                xaxis_title="Census Tract",
                yaxis_title="Domiciled Vehicles",
                barmode='stack',
                height=500,
                hovermode='x unified',
                xaxis=dict(tickangle=-45, tickfont=dict(size=8))
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating domicile distribution: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")
            
            
            
    # ========================================================================
    # CO-LOCATION AND EXPANSION OPPORTUNITY CALLBACKS
    # ========================================================================

    @app.callback(
        [
            Output('avg-retail-colocation', 'children'),
            Output('avg-rest-stops', 'children'),
            Output('avg-expansion-potential', 'children'),
            Output('high-colocation-count', 'children')
        ],
        Input('scored-data-store', 'data')
    )
    def update_colocation_metrics(scored_json):
        """Display co-location and expansion opportunity statistics"""
        if scored_json is None:
            return "0", "0", "0", "0"
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            # Co-location metrics
            avg_retail = feasible.get('retail_commercial_in_tract', pd.Series(0)).mean()
            avg_rest_stops = feasible.get('rest_stops_within_5mi', pd.Series(0)).mean()
            avg_expansion = feasible.get('estimated_park_ride_area_acres', pd.Series(0)).mean()
            
            # High co-location sites (>10 retail/commercial + rest stop access)
            high_colocation = (
                (feasible.get('retail_commercial_in_tract', pd.Series(0)) > 10) &
                (feasible.get('has_rest_stop_access', pd.Series(0)) == 1)
            ).sum()
            
            return (
                f"{avg_retail:.1f}",
                f"{avg_rest_stops:.1f}",
                f"{avg_expansion:.1f} ac",
                str(high_colocation)
            )
        except Exception as e:
            logger.error(f"Error calculating co-location metrics: {e}")
            return "N/A", "N/A", "N/A", "N/A"


    @app.callback(
        Output('colocation-opportunities-chart', 'figure'),
        Input('scored-data-store', 'data')
    )
    def create_colocation_chart(scored_json):
        """Create chart showing co-location opportunities"""
        import plotly.graph_objects as go
        
        if scored_json is None:
            return create_empty_figure("Run analysis first")
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            # Get top 30 tracts by co-location score
            feasible['colocation_score'] = (
                feasible.get('retail_commercial_in_tract', 0) * 0.5 +
                feasible.get('rest_stops_within_5mi', 0) * 5 +  # Weight rest stops higher
                feasible.get('poi_density_per_sq_mi', 0) * 0.1
            )
            
            top_tracts = feasible.nlargest(30, 'colocation_score')
            
            fig = go.Figure()
            
            # Retail/Commercial
            fig.add_trace(go.Bar(
                name='Retail/Commercial',
                x=top_tracts['GEOID'],
                y=top_tracts.get('retail_commercial_in_tract', 0),
                marker_color='#3498db'
            ))
            
            # Rest stops (scaled for visibility)
            fig.add_trace(go.Bar(
                name='Rest Stops (×5)',
                x=top_tracts['GEOID'],
                y=top_tracts.get('rest_stops_within_5mi', 0) * 5,
                marker_color='#e74c3c'
            ))
            
            # Gas stations
            fig.add_trace(go.Bar(
                name='Gas Stations',
                x=top_tracts['GEOID'],
                y=top_tracts.get('gas_stations_in_tract', 0),
                marker_color='#f39c12'
            ))
            
            fig.update_layout(
                title="Top 30 Tracts by Co-location Opportunities",
                xaxis_title="Census Tract",
                yaxis_title="Number of Facilities",
                barmode='group',
                height=500,
                hovermode='x unified',
                xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating co-location chart: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")


    @app.callback(
        Output('rest-stop-distribution-map', 'figure'),
        Input('scored-data-store', 'data')
    )
    def create_rest_stop_map(scored_json):
        """Create map showing rest stop access"""
        import plotly.express as px
        
        if scored_json is None:
            return create_initial_map()
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True].copy()
            
            if len(feasible) == 0:
                return create_empty_figure("No feasible sites")
            
            # Ensure CRS
            if feasible.crs is None:
                feasible.set_crs('EPSG:4326', inplace=True)
            
            # Create choropleth colored by rest stop priority score
            fig = px.choropleth_mapbox(
                feasible,
                geojson=feasible.geometry.__geo_interface__,
                locations=feasible.index,
                color='rest_stop_priority_score',
                color_continuous_scale='YlOrRd',
                hover_name='GEOID',
                hover_data={
                    'rest_stop_priority_score': ':.1f',
                    'rest_stops_within_5mi': True,
                    'total_rest_stop_spaces': True,
                    'interstate_rest_stops': True,
                    'has_rest_stop_access': True
                },
                labels={
                    'rest_stop_priority_score': 'Rest Stop Priority',
                    'rest_stops_within_5mi': 'Rest Stops (5mi)',
                    'total_rest_stop_spaces': 'Total Spaces',
                    'interstate_rest_stops': 'Interstate Rest Stops',
                    'has_rest_stop_access': 'Has Access'
                },
                mapbox_style="carto-positron",
                center={"lat": feasible.geometry.centroid.y.mean(),
                        "lon": feasible.geometry.centroid.x.mean()},
                zoom=8,
                opacity=0.6
            )
            
            fig.update_layout(
                title="Rest Stop Access (5-Mile Radius)",
                height=600,
                margin={"r": 0, "t": 50, "l": 0, "b": 0}
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating rest stop map: {e}", exc_info=True)
            return create_initial_map()


    @app.callback(
        Output('expansion-potential-scatter', 'figure'),
        Input('scored-data-store', 'data')
    )
    def create_expansion_scatter(scored_json):
        """Create scatter showing expansion potential vs demand"""
        import plotly.graph_objects as go
        
        if scored_json is None:
            return create_empty_figure("Run analysis first")
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            if len(feasible) == 0:
                return create_empty_figure("No feasible sites")
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=feasible.get('estimated_park_ride_area_acres', 0),
                y=feasible['demand_score'],
                mode='markers',
                marker=dict(
                    size=feasible.get('retail_commercial_in_tract', 0) * 0.5,
                    color=feasible['composite_score'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Composite<br>Score"),
                    line=dict(width=1, color='white'),
                    sizemode='diameter',
                    sizemin=4
                ),
                text=feasible['GEOID'],
                customdata=feasible.get('retail_commercial_in_tract', 0),
                hovertemplate=(
                    '<b>%{text}</b><br>' +
                    'Expansion Area: %{x:.1f} acres<br>' +
                    'Demand Score: %{y:.1f}<br>' +
                    'Retail/Commercial: %{customdata:.0f}<br>' +
                    '<extra></extra>'
                )
            ))
            
            fig.update_layout(
                title="Expansion Potential vs Demand (bubble size = retail co-location)",
                xaxis_title="Available Expansion Area (acres)",
                yaxis_title="Demand Score",
                height=500,
                hovermode='closest'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating expansion scatter: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")


    @app.callback(
        Output('colocation-characteristics-table', 'children'),
        Input('selected-sites-store', 'data')
    )
    def create_colocation_table(optimal_json):
        """Create table showing co-location characteristics for selected sites"""
        if optimal_json is None:
            return html.P("Run analysis to see selected sites", className="text-muted text-center")
        
        try:
            optimal_gdf = gpd.GeoDataFrame.from_features(json.loads(optimal_json))
            
            if len(optimal_gdf) == 0:
                return html.P("No sites selected", className="text-muted text-center")
            
            # Get full data from selector
            selector = get_selector()
            full_data = selector.gdf[selector.gdf['GEOID'].isin(optimal_gdf['GEOID'])]
            
            # Create summary table
            rows = []
            for idx, (_, site) in enumerate(full_data.iterrows()):
                rows.append(html.Tr([
                    html.Td(dbc.Badge(f"#{idx+1}", color="dark")),
                    html.Td(site['GEOID'][:10], className="font-monospace small"),
                    html.Td(f"{site.get('retail_commercial_in_tract', 0):.0f}"),
                    html.Td(f"{site.get('rest_stops_within_5mi', 0):.0f}"),
                    html.Td(f"{site.get('gas_stations_in_tract', 0):.0f}"),
                    html.Td(f"{site.get('hotels_in_tract', 0):.0f}"),
                    html.Td(f"{site.get('estimated_park_ride_area_acres', 0):.1f}")
                ]))
            
            return dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Rank"),
                    html.Th("Tract ID"),
                    html.Th("Retail/Comm.", className="small"),
                    html.Th("Rest Stops", className="small"),
                    html.Th("Gas Stations", className="small"),
                    html.Th("Hotels", className="small"),
                    html.Th("Expansion (ac)", className="small")
                ], className="table-primary")),
                html.Tbody(rows)
            ], bordered=True, hover=True, responsive=True, size='sm')
            
        except Exception as e:
            logger.error(f"Error creating co-location table: {e}", exc_info=True)
            return html.P(f"Error: {str(e)}", className="text-danger")
            
    # ========================================================================
    # ELECTRIC GRID INFRASTRUCTURE CALLBACKS
    # ========================================================================

    @app.callback(
        [
            Output('avg-grid-readiness', 'children'),
            Output('avg-solar-potential', 'children'),
            Output('high-grade-sites-count', 'children'),
            Output('avg-grid-suitability', 'children')
        ],
        Input('scored-data-store', 'data')
    )
    def update_grid_infrastructure_metrics(scored_json):
        """Display electric grid infrastructure statistics"""
        if scored_json is None:
            return "0", "0", "0", "0"
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            # Grid readiness
            avg_readiness = feasible.get('ev_infrastructure_readiness', pd.Series(0)).mean()
            
            # Solar potential
            avg_solar = feasible.get('solar_total_capacity_kw', pd.Series(0)).mean()
            
            # High-grade sites (>80% high-grade parcels)
            high_grade_count = (
                feasible.get('electric_pct_high_grade', pd.Series(0)) > 80
            ).sum()
            
            # Grid suitability
            avg_suitability = feasible.get('electric_grid_suitability', pd.Series(0)).mean()
            
            return (
                f"{avg_readiness:.1f}",
                f"{avg_solar:.0f} kW",
                str(high_grade_count),
                f"{avg_suitability:.2f}/5"
            )
        except Exception as e:
            logger.error(f"Error calculating grid infrastructure metrics: {e}")
            return "N/A", "N/A", "N/A", "N/A"


    @app.callback(
        Output('grid-readiness-map', 'figure'),
        Input('scored-data-store', 'data')
    )
    def create_grid_readiness_map(scored_json):
        """Create map showing EV infrastructure readiness"""
        import plotly.express as px
        
        if scored_json is None:
            return create_initial_map()
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True].copy()
            
            if len(feasible) == 0:
                return create_empty_figure("No feasible sites")
            
            # Ensure CRS
            if feasible.crs is None:
                feasible.set_crs('EPSG:4326', inplace=True)
            
            # Create choropleth
            fig = px.choropleth_mapbox(
                feasible,
                geojson=feasible.geometry.__geo_interface__,
                locations=feasible.index,
                color='ev_infrastructure_readiness',
                color_continuous_scale='RdYlGn',
                hover_name='GEOID',
                hover_data={
                    # Existing EV infrastructure
                    'ev_infrastructure_readiness': ':.1f',
                    'electric_grid_suitability': ':.2f',
                    'electric_pct_high_grade': ':.1f',
                    'solar_total_capacity_kw': ':.0f',
                    
                    # NEW: E3 Substation Data (in-tract)
                    'quantity_substations': ':.0f',
                    'substations_per_sq_mi': ':.2f',
                    'has_substation_access': True,
                    'median_feeder_headroom_mva': ':.1f',
                    'grid_capacity_score': ':.1f',
                    
                    # NEW: National Grid Data (5mi radius)
                    'substations_within_5mi': ':.0f',
                    'grid_available_capacity_MVA': ':.1f',
                    'ng_grid_capacity_score': ':.1f',
                    'grid_renewable_capacity_MW': ':.1f',
                    'grid_avg_utilization_pct': ':.1f',
                    'has_grid_access': True,
                    'strong_grid_access': True,
                },
                labels={
                    # Existing labels
                    'ev_infrastructure_readiness': 'EV Readiness Score',
                    'electric_grid_suitability': 'Grid Suitability (0-5)',
                    'electric_pct_high_grade': '% High-Grade Parcels',
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
                    'has_grid_access': 'Has Grid Access',
                    'strong_grid_access': 'Strong Grid Access (2+)',
                },
                mapbox_style="carto-positron",
                center={"lat": feasible.geometry.centroid.y.mean(),
                        "lon": feasible.geometry.centroid.x.mean()},
                zoom=8,
                opacity=0.6,
                range_color=[0, 100]
            )
            
            fig.update_layout(
                title="EV Infrastructure Readiness Score (0-100)",
                height=600,
                margin={"r": 0, "t": 50, "l": 0, "b": 0},
                coloraxis_colorbar=dict(title="Readiness<br>Score")
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating grid readiness map: {e}", exc_info=True)
            return create_initial_map()


    @app.callback(
        Output('solar-potential-chart', 'figure'),
        Input('scored-data-store', 'data')
    )
    def create_solar_potential_chart(scored_json):
        """Create chart showing solar potential breakdown"""
        import plotly.graph_objects as go
        
        if scored_json is None:
            return create_empty_figure("Run analysis first")
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            # Get top 30 tracts by total solar capacity
            top_tracts = feasible.nlargest(30, 'solar_total_capacity_kw')
            
            fig = go.Figure()
            
            # Building-mounted solar
            fig.add_trace(go.Bar(
                name='Building Solar',
                x=top_tracts['GEOID'],
                y=top_tracts.get('solar_building_capacity_kw', 0),
                marker_color='#f39c12'
            ))
            
            # Carport solar
            fig.add_trace(go.Bar(
                name='Carport Solar',
                x=top_tracts['GEOID'],
                y=top_tracts.get('solar_carport_capacity_kw', 0),
                marker_color='#e67e22'
            ))
            
            # Ground-mounted solar
            fig.add_trace(go.Bar(
                name='Ground Solar',
                x=top_tracts['GEOID'],
                y=top_tracts.get('solar_ground_capacity_kw', 0),
                marker_color='#d35400'
            ))
            
            fig.update_layout(
                title="Top 30 Tracts by Solar Potential (by Type)",
                xaxis_title="Census Tract",
                yaxis_title="Solar Capacity (kW)",
                barmode='stack',
                height=500,
                hovermode='x unified',
                xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating solar potential chart: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")


    @app.callback(
        Output('grid-suitability-scatter', 'figure'),
        Input('scored-data-store', 'data')
    )
    def create_grid_suitability_scatter(scored_json):
        """Create scatter showing grid suitability vs demand"""
        import plotly.graph_objects as go
        
        if scored_json is None:
            return create_empty_figure("Run analysis first")
        
        try:
            scored_gdf = gpd.GeoDataFrame.from_features(json.loads(scored_json))
            feasible = scored_gdf[scored_gdf['feasible'] == True]
            
            if len(feasible) == 0:
                return create_empty_figure("No feasible sites")
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=feasible.get('ev_infrastructure_readiness', 0),
                y=feasible['demand_score'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=feasible['composite_score'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Composite<br>Score"),
                    line=dict(width=1, color='white')
                ),
                text=feasible['GEOID'],
                customdata=feasible.get('solar_total_capacity_kw', 0),
                hovertemplate=(
                    '<b>%{text}</b><br>' +
                    'Grid Readiness: %{x:.1f}/100<br>' +
                    'Demand Score: %{y:.1f}<br>' +
                    'Solar Potential: %{customdata:.0f} kW<br>' +
                    '<extra></extra>'
                )
            ))
            
            # Add quadrant lines
            fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
            fig.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
            
            # Add quadrant labels
            annotations = [
                dict(x=25, y=75, text="High Demand<br>Low Grid", 
                     showarrow=False, font=dict(size=10, color="red")),
                dict(x=75, y=75, text="High Demand<br>High Grid<br>(IDEAL)", 
                     showarrow=False, font=dict(size=10, color="green")),
                dict(x=25, y=25, text="Low Priority", 
                     showarrow=False, font=dict(size=10, color="gray")),
                dict(x=75, y=25, text="Good Grid<br>Low Demand", 
                     showarrow=False, font=dict(size=10, color="orange"))
            ]
            
            fig.update_layout(
                title="EV Infrastructure Readiness vs Demand",
                xaxis_title="EV Infrastructure Readiness (0-100)<br>← Lower Grid Suitability | Higher Grid Suitability →",
                yaxis_title="Demand Score<br>← Lower Demand | Higher Demand →",
                height=500,
                hovermode='closest',
                annotations=annotations
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating grid suitability scatter: {e}", exc_info=True)
            return create_empty_figure(f"Error: {str(e)}")


    @app.callback(
        Output('grid-infrastructure-table', 'children'),
        Input('selected-sites-store', 'data')
    )
    def create_grid_infrastructure_table(optimal_json):
        """Create table showing grid infrastructure for selected sites"""
        if optimal_json is None:
            return html.P("Run analysis to see selected sites", className="text-muted text-center")
        
        try:
            optimal_gdf = gpd.GeoDataFrame.from_features(json.loads(optimal_json))
            
            if len(optimal_gdf) == 0:
                return html.P("No sites selected", className="text-muted text-center")
            
            # Get full data
            selector = get_selector()
            full_data = selector.gdf[selector.gdf['GEOID'].isin(optimal_gdf['GEOID'])]
            
            rows = []
            for idx, (_, site) in enumerate(full_data.iterrows()):
                readiness = site.get('ev_infrastructure_readiness', 0)
                
                # Color code readiness
                if readiness >= 70:
                    badge_color = "success"
                elif readiness >= 40:
                    badge_color = "warning"
                else:
                    badge_color = "danger"
                
                rows.append(html.Tr([
                    html.Td(dbc.Badge(f"#{idx+1}", color="dark")),
                    html.Td(site['GEOID'][:10], className="font-monospace small"),
                    html.Td(dbc.Badge(f"{readiness:.1f}", color=badge_color)),
                    html.Td(f"{site.get('electric_grid_suitability', 0):.2f}/5"),
                    html.Td(f"{site.get('electric_pct_high_grade', 0):.1f}%"),
                    html.Td(f"{site.get('solar_total_capacity_kw', 0):.0f}"),
                    html.Td(f"{site.get('solar_building_capacity_kw', 0):.0f}"),
                    html.Td(f"{site.get('solar_carport_capacity_kw', 0):.0f}")
                ]))
            
            return dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Rank"),
                    html.Th("Tract ID"),
                    html.Th("Readiness", className="small"),
                    html.Th("Grid Suit.", className="small"),
                    html.Th("% High-Grade", className="small"),
                    html.Th("Total Solar (kW)", className="small"),
                    html.Th("Building (kW)", className="small"),
                    html.Th("Carport (kW)", className="small")
                ], className="table-primary")),
                html.Tbody(rows)
            ], bordered=True, hover=True, responsive=True, size='sm')
            
        except Exception as e:
            logger.error(f"Error creating grid infrastructure table: {e}", exc_info=True)
            return html.P(f"Error: {str(e)}", className="text-danger")

    @app.callback(
        Output('download-export', 'data'),
        Input('export-btn', 'n_clicks'),
        State('selected-sites-store', 'data'),
        prevent_initial_call=True
    )
    def export_optimal_sites(n_clicks, selected_sites_json):
        """Export the currently selected optimal sites (tract-level).

        Notes
        - We keep score fields from the selected-sites store (those are computed at runtime).
        - We back-fill raw/source columns from selector.gdf (e.g., total_pop) because the
          stored FeatureCollection properties can be trimmed/incomplete.
        - Export is CSV to avoid needing Excel writer engines on Render.
        """
        if not selected_sites_json:
            raise PreventUpdate

        import json
        import pandas as pd

        data = json.loads(selected_sites_json) if isinstance(selected_sites_json, str) else selected_sites_json
        features = data.get('features', []) or []
        if not features:
            raise PreventUpdate

        # 1) Start from FeatureCollection properties so computed scores remain available
        props_rows = [f.get('properties', {}) or {} for f in features]
        df_props = pd.DataFrame(props_rows)

        if 'GEOID' not in df_props.columns:
            raise PreventUpdate

        df_props['GEOID'] = df_props['GEOID'].astype(str)

        # 2) Pull raw/source fields from the full selector dataframe to back-fill missing values
        selector = get_selector()
        if selector is None or not hasattr(selector, 'gdf'):
            raise PreventUpdate

        geoid_list = df_props['GEOID'].dropna().astype(str).unique().tolist()

        desired_raw_cols = [
            'GEOID',
            'total_pop',
            'Heavy_Duty', 'Light_Duty', 'Medium_Duty',
            'avg_stop_duration_minutes',
            'Heavy_Duty__AM_Peak_6_10',
            'Heavy_Duty__Evening_19_6',
            'Heavy_Duty__Midday_10_15',
            'Heavy_Duty__PM_Peak_15_19',
            'poi_density_per_sq_mi',
            'pct_ej_block_groups',
            'rest_stop_density',
            'substations_per_sq_mi',
            'total_vehicles_domiciled',
            'charging_type'
        ]
        raw_cols_present = [c for c in desired_raw_cols if c in selector.gdf.columns]
        raw_df = selector.gdf[selector.gdf['GEOID'].astype(str).isin(geoid_list)][raw_cols_present].copy()
        if 'GEOID' in raw_df.columns:
            raw_df['GEOID'] = raw_df['GEOID'].astype(str)

        df = df_props.merge(raw_df, on='GEOID', how='left', suffixes=('', '_raw'))

        # 3) Prefer values already in df_props; fill missing/blank from raw
        for c in desired_raw_cols:
            if c == 'GEOID':
                continue
            c_raw = f"{c}_raw"
            if c in df.columns and c_raw in df.columns:
                # treat blank strings as missing
                df[c] = df[c].replace('', pd.NA)
                df[c] = df[c].where(df[c].notna(), df[c_raw])
                df.drop(columns=[c_raw], inplace=True)
            elif c not in df.columns and c_raw in df.columns:
                df.rename(columns={c_raw: c}, inplace=True)

        # 4) Bin domicile values for export (privacy-friendly)
        domicile_bins = [0, 25, 50, 100, 200, 500, float('inf')]
        domicile_labels = ['0-25', '25-50', '50-100', '100-200', '200-500', '500+']
        if 'total_vehicles_domiciled' in df.columns:
            df['total_vehicles_domiciled'] = pd.cut(
                pd.to_numeric(df['total_vehicles_domiciled'], errors='coerce'),
                bins=domicile_bins,
                labels=domicile_labels,
                include_lowest=True,
                right=False
            ).astype('object')

        # 5) Rank: sort by composite_score desc when available
        if 'composite_score' in df.columns:
            df['composite_score'] = pd.to_numeric(df['composite_score'], errors='coerce')
            df = df.sort_values('composite_score', ascending=False, na_position='last')

        df.insert(0, 'rank', range(1, len(df) + 1))

        # Output schema requested
        export_cols = [
            'rank', 'GEOID', 'charging_type',
            'composite_score', 'demand_score', 'infrastructure_score',
            'accessibility_score', 'equity_feasibility_score',
            'total_pop', 'Heavy_Duty', 'Light_Duty', 'Medium_Duty',
            'avg_stop_duration_minutes',
            'Heavy_Duty__AM_Peak_6_10',
            'Heavy_Duty__Evening_19_6',
            'Heavy_Duty__Midday_10_15',
            'Heavy_Duty__PM_Peak_15_19',
            'poi_density_per_sq_mi', 'pct_ej_block_groups',
            'rest_stop_density', 'substations_per_sq_mi',
            'total_vehicles_domiciled'
        ]

        out = pd.DataFrame({c: df[c] if c in df.columns else pd.NA for c in export_cols})

        return dcc.send_data_frame(out.to_csv, 'optimal_sites_export.csv', index=False)
