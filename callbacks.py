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

    

    @app.callback(
        Output('temporal-subweight-validation', 'children'),
        [Input('temporal-stability-subweight', 'value'),
         Input('temporal-peak-subweight', 'value')]
    )
    def validate_temporal_subweights(stability, peak):
        """Validate that temporal sub-weights sum to 100."""
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
         State('min-distance-slider', 'value'),
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
                     n_sites, min_dist, min_person_trips, secondary_buffer_value, rural_only_value,
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
                    'commercial_industrial_weight': commercial_w / equity_sub_sum,
                    'protected_penalty_weight': protected_penalty_w / equity_sub_sum
                }
            else:
                # Treat all-zeros as "disable this section"
                selector.config['equity_weights'] = {
                    'ej_priority_weight': 0.0,
                    'landuse_suit_weight': 0.0,
                    'commercial_industrial_weight': 0.0,
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
                min_distance_mi=float(min_dist) if min_dist is not None else 0
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

        Reliability notes:
        - We always rebuild the figure from the latest stores so the map stays consistent
          with the latest analysis result and the site rankings table.
        - When the user clicks a tract GEOID link, we rebuild and then update the viewport
          (center/zoom). This avoids edge cases where Patch updates can be dropped and the
          map appears "stuck" on a previous run.
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

            # Always rebuild from the latest stores first (keeps map/table in sync)
            fig = create_optimal_sites_map(scored_gdf, optimal_gdf)

            # If a tract GEOID link was clicked, zoom to that tract.
            if isinstance(triggered_id, dict) and triggered_id.get('type') == 'tract-link':
                clicked_geoid = triggered_id.get('index')
                clicked_geoid_str = str(clicked_geoid) if clicked_geoid is not None else None

                target = None
                if clicked_geoid_str and 'GEOID' in scored_gdf.columns:
                    target = scored_gdf[scored_gdf['GEOID'].astype(str) == clicked_geoid_str]
                # Fallback: sometimes users click a GEOID that's only present in selected set
                if (target is None or len(target) == 0) and clicked_geoid_str and 'GEOID' in optimal_gdf.columns:
                    target = optimal_gdf[optimal_gdf['GEOID'].astype(str) == clicked_geoid_str]

                if target is not None and len(target) > 0:
                    try:
                        centroid = target.geometry.iloc[0].centroid
                        fig.update_layout(
                            mapbox=dict(
                                center={'lat': float(centroid.y), 'lon': float(centroid.x)},
                                zoom=11
                            )
                        )
                    except Exception:
                        # If centroid fails for any reason, just return the rebuilt fig
                        pass

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
            # NOTE: In this secondary-corridor tool, `charging_type` is currently the
            # long-distance-share classifier from the console log (long_distance vs other).
            # Keep the mapping explicit so the table doesn't default to "Unclassified".
            type_icons = {
                'long_distance': ('🛣️', 'Long-distance', 'warning'),
                'other': ('🏙️', 'Other', 'secondary'),
                'unclassified': ('❓', 'Unclassified', 'secondary')
            }

            # Create table rows
            rows = []
            for idx, row in optimal_gdf.iterrows():
                raw_ctype = row.get('charging_type', None)
                ctype = str(raw_ctype).strip().lower() if raw_ctype is not None else ''
                if ctype in ('', 'none', 'nan'):
                    ctype = 'unclassified'
                icon, type_label, badge_color = type_icons.get(ctype, type_icons['unclassified'])
                # Rural flag (robust to multiple possible schemas)
                is_rural = False
                if 'rural_flag' in row and row.get('rural_flag') is not None:
                    try:
                        is_rural = bool(int(row.get('rural_flag')))
                    except Exception:
                        is_rural = bool(row.get('rural_flag'))
                elif 'is_rural' in row and row.get('is_rural') is not None:
                    is_rural = bool(row.get('is_rural'))
                elif 'rural' in row and row.get('rural') is not None:
                    is_rural = bool(row.get('rural'))
                elif row.get('urban_rural_context') is not None:
                    is_rural = str(row.get('urban_rural_context')).strip().lower() == 'rural'

                
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
                            dbc.Badge(
                                'Rural' if is_rural else 'Non-rural',
                                color=('success' if is_rural else 'secondary'),
                                className='me-1'
                            ),
                            className='text-center text-nowrap'
                        ),
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
                        html.Th("Rural", className="text-center"),
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
            # 'Heavy_Duty', 'Light_Duty', 'Medium_Duty',
            # 'avg_stop_duration_minutes',
            # 'Heavy_Duty__AM_Peak_6_10',
            # 'Heavy_Duty__Evening_19_6',
            # 'Heavy_Duty__Midday_10_15',
            # 'Heavy_Duty__PM_Peak_15_19',
            'equity_0_trips', 'equity_1_trips', 'dow_1_trips', 'dow_2_3_trips', '%_long_distance_trips','rural_flag',
            # 'government_social_services_within_5mi','grocery_stores_within_5mi','park_ride_spaces_within_5mi',
            'poi_density_per_sq_mi',
            'pct_ej_block_groups',
            'rest_stop_density',
            # 'substations_per_sq_mi',
            # 'total_vehicles_domiciled',
            'charging_type','median_feeder_headroom_mva'
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

        # # 4) Bin domicile values for export (privacy-friendly)
        # domicile_bins = [0, 25, 50, 100, 200, 500, float('inf')]
        # domicile_labels = ['0-25', '25-50', '50-100', '100-200', '200-500', '500+']
        # if 'total_vehicles_domiciled' in df.columns:
        #     df['total_vehicles_domiciled'] = pd.cut(
        #         pd.to_numeric(df['total_vehicles_domiciled'], errors='coerce'),
        #         bins=domicile_bins,
        #         labels=domicile_labels,
        #         include_lowest=True,
        #         right=False
        #     ).astype('object')

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
            'total_pop', 'equity_0_trips', 'equity_1_trips', 'dow_1_trips', 'dow_2_3_trips', '%_long_distance_trips','rural_flag',
            # 'Heavy_Duty', 'Light_Duty', 'Medium_Duty',
            # 'avg_stop_duration_minutes',
            # 'Heavy_Duty__AM_Peak_6_10',
            # 'Heavy_Duty__Evening_19_6',
            # 'Heavy_Duty__Midday_10_15',
            # 'Heavy_Duty__PM_Peak_15_19',
            'poi_density_per_sq_mi', 'pct_ej_block_groups',
            'rest_stop_density', 'median_feeder_headroom_mva'
            #'nearest_truck_charger_mi',
            # 'substations_per_sq_mi',
            # 'total_vehicles_domiciled'
        ]

        out = pd.DataFrame({c: df[c] if c in df.columns else pd.NA for c in export_cols})

        return dcc.send_data_frame(out.to_csv, 'optimal_sites_export.csv', index=False)
