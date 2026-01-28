from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# ============================================================================
# STYLING AND LAYOUT COMPONENTS
# ============================================================================

def create_navbar() -> dbc.Navbar:
    """Create professional navigation bar with logout button"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                # Left side - App title
                dbc.Col([
                    html.I(className="fas fa-charging-station fa-2x text-white me-3"),
                    html.Div([
                        html.H3("Massachusetts Secondary Network Charging Site Selector",
                                className="mb-0 text-white"),
                        html.Small(
                            "Infrastructure Planning & Analysis Tool",
                            className="text-white-50"
                        )
                    ])
                ], width="auto", className="d-flex align-items-center"),

                # Right side - "Powered by LOCUS" + Logout
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Small(
                                    "Powered by",
                                    className="text-white-50 me-2"
                                ),
                                html.Img(
                                    src="/dash/assets/locus-logo_ko_1000.webp",
                                    style={
                                        "height": "26px",
                                        "width": "auto",
                                        "filter": "drop-shadow(0px 1px 1px rgba(0,0,0,0.25))",
                                    },
                                    alt="LOCUS"
                                ),
                            ],
                            className="d-flex align-items-center"
                        ),
                        html.A(
                            [
                                html.I(className="fas fa-sign-out-alt me-2"),
                                "Logout"
                            ],
                            href="/logout",
                            className="btn btn-outline-light btn-sm ms-3",
                            style={"textDecoration": "none"}
                        )
                    ],
                    width="auto",
                    className="d-flex align-items-center ms-auto"
                )
               
            ], className="g-0 w-100 justify-content-between")
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-4 shadow"
    )

def create_metric_card(title: str, value: str, icon: str,
                       color: str = "primary") -> dbc.Card:
    """Create a metric display card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.I(className=f"{icon} fa-2x text-{color} mb-2"),
                    html.H3(value, className="mb-0 mt-2"),
                    html.P(title, className="text-muted mb-0 small")
                ], className="text-center")
            ])
        ])
    ], className="shadow-sm border-0 h-100")

def create_control_section(title: str, children: list,
                           icon: str = "fas fa-cog") -> dbc.Card:
    """Create a collapsible control section"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className=f"{icon} me-2"),
            html.Strong(title)
        ], className="bg-light"),
        dbc.CardBody(children)
    ], className="mb-3 shadow-sm border-0")

def create_weight_slider(id_suffix: str, label: str,
                         default_value: int) -> html.Div:
    """Create a styled weight slider with live feedback"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label(label, className="fw-bold small mb-1"),
            ], width=8),
            dbc.Col([
                dbc.Badge(f"{default_value}%",
                          id=f'{id_suffix}-badge',
                          color="primary",
                          className="float-end")
            ], width=4)
        ]),
        dcc.Slider(
            id=f'{id_suffix}-weight',
            min=0, max=100, step=5, value=default_value,
            marks={i: {'label': f'{i}%', 'style': {'fontSize': '10px'}}
                   for i in range(0, 101, 25)},
            className="mb-3",
            tooltip={"placement": "bottom", "always_visible": False}
        )
    ], className="mb-3")

def create_constraint_input(id_suffix: str, label: str,
                            default_value: float, step: float = 0.1,
                            units: str = "") -> dbc.InputGroup:
    """Create a styled constraint input"""
    input_group_items = [
        dbc.InputGroupText(label, className="small", style={"minWidth": "140px"}),
        dbc.Input(
            id=f'{id_suffix}-input',
            type='number',
            value=default_value,
            step=step,
            className="form-control-sm"
        )
    ]
    
    if units:
        input_group_items.append(
            dbc.InputGroupText(units, className="small", style={"minWidth": "50px"})
        )
    
    return dbc.InputGroup(input_group_items, size="sm", className="mb-2")

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
    
"""
Additional helper functions for sub-component weight controls
Add these to your existing layout.py
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def create_subweight_input(id_suffix: str, label: str,
                           default_value: int, step: int = 1,
                           min_value: int = 0, max_value: int = 100) -> dbc.Row:
    """Create a sub-component weight input with label (integer points 0-100)."""
    return dbc.Row([
        dbc.Col([
            html.Label(label, className="small text-muted mb-0"),
        ], width=7),
        dbc.Col([
            dbc.Input(
                id=f'{id_suffix}-subweight',
                type='number',
                value=default_value,
                step=step,
                min=min_value,
                max=max_value,
                size="sm",
                className="text-end"
            )
        ], width=5)
    ], className="mb-2 align-items-center")


def create_demand_subweights_section() -> html.Div:
    """Create collapsible section for demand sub-component weights"""
    return dbc.Collapse([
        dbc.Card([
            dbc.CardBody([
                html.P("Trip Purpose Weights:", className="small fw-bold text-primary mb-2"),
                html.Small("These must sum to 100 within this category (or set to 0 to exclude a sub-factor)",
                          className="text-muted d-block mb-2"),

                create_subweight_input('home-end', 'Home End', 40),
                create_subweight_input('workplace-end', 'Workplace End', 40),
                create_subweight_input('other-end', 'Other End', 20),

                html.Div(id='purpose-subweight-validation', className="mb-2"),

                html.Hr(className="my-2"),

                html.P("Day of Week Weights:", className="small fw-bold text-primary mb-2"),

                create_subweight_input('weekday', 'Weekday Trips', 70),
                create_subweight_input('weekend', 'Weekend Trips', 30),

                html.Div(id='dow-subweight-validation', className="mb-2"),

                html.Hr(className="my-2"),

                html.P("Equity Community Weights:", className="small fw-bold text-primary mb-2"),

                create_subweight_input('equity-community', 'Trips made by Equity Community', 50),
                create_subweight_input('non-equity-community', 'Trips made by Non-Equity Community', 50),

                html.Div(id='equity-trip-subweight-validation', className="mb-2"),

                html.Hr(className="my-2"),

                html.P("Temporal Pattern Weights:", className="small fw-bold text-warning mb-2"),
                # html.Small("How demand varies throughout the day (must sum to 100 - or set to 0 to not be considered)",
                #           className="text-muted d-block mb-2"),

                create_subweight_input('temporal-stability', 'Demand Stability', 60),
                html.Small("Weight for stable/uniform demand",
                          className="text-muted d-block mb-2", style={"fontSize": "10px"}),

                create_subweight_input('temporal-peak', 'Peak Intensity', 40),
                html.Small("Weight for peak demand periods",
                          className="text-muted d-block mb-2", style={"fontSize": "10px"}),

                html.Div(id='temporal-subweight-validation', className="mb-2"),

                dbc.Button([
                    html.I(className="fas fa-undo me-1"),
                    "Reset Demand Defaults"
                ], id="reset-demand-subweights-btn",
                   color="secondary", size="sm", outline=True,
                   className="w-100 mt-2")
            ], className="p-2")
        ], className="border-start border-primary border-3")
    ], id="demand-subweights-collapse", is_open=False)



def create_infrastructure_subweights_section() -> html.Div:
    """Create collapsible section for infrastructure sub-component weights"""
    return dbc.Collapse([
        dbc.Card([
            dbc.CardBody([
                html.P("Infrastructure Component Weights:", className="small fw-bold text-success mb-2"),
                html.Small("Set relative importance of each factor (sum to 100; set to 0 to exclude).",
                          className="text-muted d-block mb-2"),

                create_subweight_input('ev-gap', 'Ability to Fill Gaps in Charging Network', 45),
                html.Small("Higher = prioritize areas with fewer existing chargers",
                          className="text-muted d-block mb-2", style={"fontSize": "10px"}),

                create_subweight_input('park-ride', 'Co-location with transit & transit parking lots', 30),
                html.Small("Shared infrastructure potential (consistent 5-mi buffer measure)",
                          className="text-muted d-block mb-2", style={"fontSize": "10px"}),

                create_subweight_input('government', 'Co-location with government & social services', 25),
                html.Small("Government/social service presence (consistent 5-mi buffer measure)",
                          className="text-muted d-block mb-2", style={"fontSize": "10px"}),

                html.Div(id='infrastructure-subweight-validation', className="mt-2"),

                dbc.Button([
                    html.I(className="fas fa-undo me-1"),
                    "Reset Infrastructure Defaults"
                ], id="reset-infrastructure-subweights-btn",
                   color="secondary", size="sm", outline=True,
                   className="w-100 mt-2")
            ], className="p-2")
        ], className="border-start border-success border-3")
    ], id="infrastructure-subweights-collapse", is_open=False)


def create_accessibility_subweights_section() -> html.Div:
    """Create collapsible section for accessibility sub-component weights"""
    return dbc.Collapse([
        dbc.Card([
            dbc.CardBody([
                html.P("Accessibility Component Weights:", className="small fw-bold text-danger mb-2"),
                html.Small("Set relative importance of each factor (sum to 100; set to 0 to exclude).",
                          className="text-muted d-block mb-2"),

                create_subweight_input('network-density', 'Network Density', 50),
                create_subweight_input('grocery', 'Co-location with grocery stores', 25),
                create_subweight_input('gas-station', 'Co-location with gas stations', 25),

                html.Div(id='accessibility-subweight-validation', className="mt-2"),

                dbc.Button([
                    html.I(className="fas fa-undo me-1"),
                    "Reset Accessibility Defaults"
                ], id="reset-accessibility-subweights-btn",
                   color="secondary", size="sm", outline=True,
                   className="w-100 mt-2")
            ], className="p-2")
        ], className="border-start border-danger border-3")
    ], id="accessibility-subweights-collapse", is_open=False)


def create_equity_subweights_section() -> html.Div:
    """Create collapsible section for equity/feasibility sub-component weights"""
    return dbc.Collapse([
        dbc.Card([
            dbc.CardBody([
                html.P("Equity & Environmental Weights:", className="small fw-bold text-info mb-2"),
                html.Small("Positive factors (benefits):", 
                          className="text-muted d-block mb-2"),
                
                create_subweight_input('ej-priority', 'EJ Priority Access', 40),
                create_subweight_input('landuse-suit', 'Land Use Suitability', 35),
                create_subweight_input('commercial', 'Commercial/Industrial', 15),
                
                html.Hr(className="my-2"),
                html.Small("Negative factors (penalties):", 
                          className="text-muted d-block mb-2"),
                
                create_subweight_input('protected-penalty', 'Protected Land Penalty', 10),
                html.Small("Applied as deduction", 
                          className="text-muted d-block mb-2", style={"fontSize": "10px"}),
                
                html.Div(id='equity-subweight-validation', className="mt-2"),
                
                dbc.Button([
                    html.I(className="fas fa-undo me-1"),
                    "Reset Equity Defaults"
                ], id="reset-equity-subweights-btn", 
                   color="secondary", size="sm", outline=True, 
                   className="w-100 mt-2")
            ], className="p-2")
        ], className="border-start border-info border-3")
    ], id="equity-subweights-collapse", is_open=False)


def create_weight_slider_with_expand(id_suffix: str, label: str, 
                                     default_value: int, 
                                     has_subweights: bool = False) -> html.Div:
    """
    Create a weight slider with optional expand button for sub-weights
    """
    slider_row = dbc.Row([
        dbc.Col([
            html.Label(label, className="fw-bold small mb-1"),
        ], width=6 if has_subweights else 8),
        dbc.Col([
            dbc.Badge(f"{default_value}%",
                      id=f'{id_suffix}-badge',
                      color="primary",
                      className="float-end")
        ], width=3 if has_subweights else 4),
        dbc.Col([
            dbc.Button(
                html.I(className="fas fa-chevron-down"),
                id=f'{id_suffix}-expand-btn',
                color="link",
                size="sm",
                className="p-0"
            ) if has_subweights else None
        ], width=3) if has_subweights else None
    ], className="align-items-center")
    
    slider = dcc.Slider(
        id=f'{id_suffix}-weight',
        min=0, max=100, step=5, value=default_value,
        marks={i: {'label': f'{i}%', 'style': {'fontSize': '10px'}}
               for i in range(0, 101, 25)},
        className="mb-2",
        tooltip={"placement": "bottom", "always_visible": False}
    )
    
    return html.Div([
        slider_row,
        slider
    ], className="mb-3")
    
    


# ============================================================================
# MAIN LAYOUT FUNCTION
# ============================================================================

def create_layout():
    """Create the complete dashboard layout"""
    return html.Div([
        create_navbar(),

        dbc.Container([
            # Outer tabs wrapper - Home and Analysis Dashboard
            dbc.Tabs([
                # ===============================================================
                # TAB 1: HOME / INTRODUCTION
                # ===============================================================
                dbc.Tab([
                    dbc.Container([
                        dbc.Row([
                            dbc.Col([
                                html.H2("Welcome to the MA Secondary Network Charging Site Selector",
                                        className="mb-4 mt-4"),
                                html.Hr(),

                                # What the tool does
                                html.H4([html.I(className="fas fa-info-circle me-2"),
                                         "What This Decision Support Tool Does"], className="mt-4 mb-3"),
                                html.P([
                                    "This decision support tool helps identify optimal locations for light-duty electric passenger vehicles ",
                                    "charging infrastructure across Massachusetts using multi-criteria analysis. ",
                                    "It evaluates census tracts based on activity demand, electrical infrastructure ",
                                    "capacity, transportation accessibility, and equity considerations."
                                ], className="lead"),

                                # Key capabilities
                                html.H4([html.I(className="fas fa-star me-2"),
                                         "Key Capabilities"], className="mt-4 mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.I(className="fas fa-sliders-h fa-2x text-primary mb-3"),
                                                html.H5("Customizable Weights", className="card-title"),
                                                html.P("Adjust scoring weights for demand, infrastructure, "
                                                       "accessibility, and equity factors", className="small")
                                            ])
                                        ], className="text-center h-100 shadow-sm")
                                    ], md=3),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.I(className="fas fa-map-marked-alt fa-2x text-success mb-3"),
                                                html.H5("Interactive Maps", className="card-title"),
                                                html.P("Visualize scoring components and optimal site locations "
                                                       "across Massachusetts", className="small")
                                            ])
                                        ], className="text-center h-100 shadow-sm")
                                    ], md=3),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.I(className="fas fa-chart-bar fa-2x text-info mb-3"),
                                                html.H5("Analytics Dashboard", className="card-title"),
                                                html.P("Compare sites with distribution charts, rankings, "
                                                       "and radar plots", className="small")
                                            ])
                                        ], className="text-center h-100 shadow-sm")
                                    ], md=3),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.I(className="fas fa-cogs fa-2x text-warning mb-3"),
                                                html.H5("Constraint Filtering", className="card-title"),
                                                html.P("Apply feasibility constraints based on tract-level limits "
                                                    #    "(e.g., max facility densities)"
                                                       , className="small")
                                            ])
                                        ], className="text-center h-100 shadow-sm")
                                    ], md=3)
                                ], className="mb-4"),
                                
                                # Data sources
                                html.H4([html.I(className="fas fa-database me-2"), "Data Sources"],
                                        className="mb-3 mt-4"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-truck me-2 text-primary"),
                                        html.Strong("LOCUS: "),
                                        "Person trip ends by purpose, weekday/weekend, equity community and time of day"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-bolt me-2 text-warning"),
                                        html.Strong("National Grid Massachusetts System Data Portal: "),
                                        "3-phase feeder network"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-map me-2 text-success"),
                                        html.Strong("MassGIS: "),
                                        "Land use/land cover, parcel data, and property tax assessments"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-users me-2 text-info"),
                                        html.Strong("MassGIS Environmental Justice: "),
                                        "EJ population designations (2020 Census block groups) including income, minority, and English isolation criteria"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-road me-2 text-danger"),
                                        html.Strong("MassDOT Traffic Volume and Classification: "),
                                        "AADT data"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-location-dot me-2 text-secondary"),
                                        html.Strong("OpenStreetMap: "),
                                        "POI locations (gas stations, grocery stores, government spaces)"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-chart-area me-2 text-primary"),
                                        html.Strong("EPA Smart Location Database: "),
                                        "Urban form metrics (density, transit access, job accessibility)"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-charging-station me-2 text-success"),
                                        html.Strong("Alternative Fuels Data Center: "),
                                        "Existing EV charging station locations"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-train me-2 text-warning"),
                                        html.Strong("MassDOT: "),
                                        "Co-location with transit & transit parking lots"
                                    ]),
                                    # dbc.ListGroupItem([
                                    #     html.I(className="fas fa-clock me-2 text-primary"),
                                    #     html.Strong("Stop Duration/Air Quality Improvement Potential Analysis: "),
                                    #     "Post-trip stop duration, translating to air quality improvement potential from LOCUS data - only trips with stops ≥ 30 minutes qualify as charging opportunities"
                                    # ])
                                ], className="mb-4"),

                                # User manual
                                html.H4([html.I(className="fas fa-book me-2"),
                                         "Quick Start Guide"], className="mt-4 mb-3"),
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Ol([
                                            html.Li([
                                                html.Strong("Adjust Scoring Weights: "),
                                                "Use the sliders in the left panel to set priorities for demand, "
                                                "infrastructure, accessibility, and equity (must sum to 100%)"
                                            ], className="mb-2"),
                                            html.Li([
                                                html.Strong("Configure Site Selection: "),
                                                "Choose the number of optimal sites to identify"
                                            ], className="mb-2"),
                                            html.Li([
                                                html.Strong("Set Constraints: "),
                                                "Define minimum trip activity thresholds and toggle on if secondary network nearby, rural flag and median feeder headroom constraints"
                                            ], className="mb-2"),
                                            html.Li([
                                                html.Strong("Run Analysis: "),
                                                "Click the 'Run Analysis' button to calculate scores and identify "
                                                "optimal sites"
                                            ], className="mb-2"),
                                            html.Li([
                                                html.Strong("Explore Results: "),
                                                "Navigate through the analysis tabs to view maps, rankings, and "
                                                "detailed component breakdowns"
                                            ], className="mb-2"),
                                            html.Li([
                                                html.Strong("Export Data: "),
                                                "Use the Export button to download results for further analysis"
                                            ])
                                        ])
                                    ])
                                ], className="bg-light"),

                                # Call to action
                                html.Div([
                                    html.Hr(className="my-4"),
                                    dbc.Button([
                                        html.I(className="fas fa-arrow-right me-2"),
                                        "Go to Analysis Dashboard"
                                    ], color="primary", size="lg", id="go-to-analysis-btn",
                                        className="mb-4")
                                ], className="text-center")

                            ], md=10, className="mx-auto")
                        ])
                    ], fluid=True, className="py-4")
                ], label="Home", tab_id="tab-home", label_style={"font-weight": "bold"}),

                # ===============================================================
                # TAB 2: ANALYSIS DASHBOARD
                # ===============================================================
                dbc.Tab([
                    # Summary metrics row
                    dbc.Row([
                        dbc.Col([
                            html.Div(id='summary-metrics', className="mb-4")
                        ])
                    ]),

                    # Main content
                    dbc.Row([
                        # Left sidebar - Controls
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    # Scoring Weights Section

                                    create_control_section(
                                        "Scoring Weights",
                                        [
                                            # Demand with sub-weights
                                            create_weight_slider_with_expand('demand', 'Demand', 40, has_subweights=True),
                                            create_demand_subweights_section(),
                                            
                                            # Infrastructure with sub-weights  
                                            create_weight_slider_with_expand('infrastructure', 'Infrastructure', 25, has_subweights=True),
                                            create_infrastructure_subweights_section(),
                                            
                                            # Accessibility with sub-weights
                                            create_weight_slider_with_expand('accessibility', 'Accessibility', 20, has_subweights=True),
                                            create_accessibility_subweights_section(),
                                            
                                            # Equity with sub-weights
                                            create_weight_slider_with_expand('equity', 'Equity & Environmental', 15, has_subweights=True),
                                            create_equity_subweights_section(),
                                            
                                            html.Hr(className="my-2"),
                                            html.Div(id='weight-validation', className="mt-2")
                                        ],
                                        icon="fas fa-balance-scale"
                                    ),

                                    # Site Selection Section
                                    create_control_section(
                                        "Site Selection",
                                        [
                                            create_constraint_input(
                                                'n-sites',
                                                'Number of Sites',
                                                4,
                                                step=1,
                                                units='sites'
                                            ),
                                            html.Hr(className="my-3"),
                                            html.Label("Minimum Distance Between Sites",
                                                       className="fw-bold small mb-1"),
                                            dcc.Slider(
                                                id='min-distance-slider',
                                                # Allow users to set 0 mi (no separation) and fine-tune with 2-mi steps
                                                min=0, max=50, step=2, value=10,
                                                marks={i: f'{i}mi' for i in range(0, 51, 10)},
                                                tooltip={"placement": "bottom"}
                                            ),
                                        ],
                                        icon="fas fa-map-marker-alt"
                                    ),

                                    # Constraints Section
                                    create_control_section(
                                        "Feasibility Constraints",
                                        [
                                            create_constraint_input(
                                                'min-person',
                                                'Min Person Trips/Day',
                                                10,
                                                step=1,
                                                units='trips'
                                            ),
                                            # NEW: Optional buffer constraint for secondary network
                                            html.Div([
                                                dbc.Checklist(
                                                    id='secondary-buffer-toggle',
                                                    options=[{
                                                        'label': 'Only include tracts within buffer area of secondary network',
                                                        'value': 'within'
                                                    }],
                                                    value=['within'],
                                                    switch=True,
                                                    className="small"
                                                )
                                            ], className="mt-2"),

                                            # NEW: Optional rural-only constraint
                                            html.Div([
                                                dbc.Checklist(
                                                    id='rural-only-toggle',
                                                    options=[{
                                                        'label': 'Only include rural tracts',
                                                        'value': 'rural'
                                                    }],
                                                    value=[],
                                                    switch=True,
                                                    className="small"
                                                )
                                            ], className="mt-2"),

                                            # Optional grid headroom constraint
                                            html.Div([
                                                dbc.Checklist(
                                                    id='exclude-zero-headroom-toggle',
                                                    options=[{
                                                        'label': 'Only include tracts with >0 feeder headroom',
                                                        'value': 'exclude'
                                                    }],
                                                    value=[],
                                                    switch=True,
                                                    className="small"
                                                )
                                            ], className="mt-2")

                                    ],
                                        icon="fas fa-check-circle"
                                    ),

                                    # Charging Type Quick Reference (Optional but helpful)
                                    dbc.Card([
                                        dbc.CardHeader([
                                            html.I(className="fas fa-info-circle me-2"),
                                            html.Strong("Charging Type Guide")
                                        ], className="bg-light"),
                                        dbc.CardBody([
                                            html.Div([
                                                html.Div([
                                                    html.Span("🛣️", className="me-2"),
                                                    html.Strong("Long-distance", className="small text-success")
                                                ], className="mb-1"),
                                                html.P("Areas with a higher concentration of long-distance (>50 mi) trip ends", 
                                                       className="small text-muted mb-2", style={"marginLeft": "30px"}),

                                                html.Div([
                                                    html.Span("🏙️", className="me-2"),
                                                    html.Strong("Other", className="small text-secondary")
                                                ], className="mb-1"),
                                                html.P("Areas with fewer long-distance (>50 mi) trip ends", 
                                                       className="small text-muted mb-0", style={"marginLeft": "30px"})
                                            ])
                                        ], className="p-2")
                                    ], className="mb-3 shadow-sm border-0"),

                                    # # Stop Duration Info (OPTIONAL - adds visual explanation)
                                    # dbc.Card([
                                        # dbc.CardHeader([
                                            # html.I(className="fas fa-clock me-2"),
                                            # html.Strong("Stop Duration Filter")
                                        # ], className="bg-light"),
                                        # dbc.CardBody([
                                            # html.P("Only trips with stops ≥ 30 min count as charging opportunities.", 
                                                   # className="small mb-2"),
                                            # dbc.Row([
                                                # dbc.Col([
                                                    # html.Small("Avg Stop:", className="text-muted d-block"),
                                                    # html.H6("--", id="avg-stop-duration", className="mb-0 text-primary")
                                                # ], width=6),
                                                # dbc.Col([
                                                    # html.Small("% Eligible:", className="text-muted d-block"),
                                                    # html.H6("--", id="pct-eligible-trips", className="mb-0 text-success")
                                                # ], width=6)
                                            # ])
                                        # ], className="p-2")
                                    # ], className="mb-3 shadow-sm border-0"),
                                    
                                    # # Temporal Demand Patterns Info (NEW)
                                    # dbc.Card([
                                        # dbc.CardHeader([
                                            # html.I(className="fas fa-chart-line me-2"),
                                            # html.Strong("Temporal Demand Patterns")
                                        # ], className="bg-light"),
                                        # dbc.CardBody([
                                            # html.P("How demand varies throughout the day affects charging strategy.", 
                                                   # className="small mb-2"),
                                            # dbc.Row([
                                                # dbc.Col([
                                                    # html.Small("Avg Uniformity:", className="text-muted d-block"),
                                                    # html.H6("--", id="avg-demand-uniformity", className="mb-0 text-info")
                                                # ], width=6),
                                                # dbc.Col([
                                                    # html.Small("Avg Peak:", className="text-muted d-block"),
                                                    # html.H6("--", id="avg-peak-intensity", className="mb-0 text-warning")
                                                # ], width=6)
                                            # ]),
                                            # html.Hr(className="my-2"),
                                            # html.Small("Recommended Charging Types:", className="text-muted d-block mb-1"),
                                            # html.Div(id='recommended-charging-breakdown', className="small")
                                        # ], className="p-2")
                                    # ], className="mb-3 shadow-sm border-0"),
                                    
                                    
                                    # Action buttons
                                    html.Hr(),
                                    dbc.ButtonGroup([
                                        dbc.Button(
                                            [html.I(className="fas fa-play me-2"), "Run Analysis"],
                                            id="run-analysis-btn",
                                            color="success",
                                            size="lg",
                                            className="w-100"
                                        )
                                    ], className="w-100 mb-2"),

                                    dbc.ButtonGroup([
                                        dbc.Button(
                                            [html.I(className="fas fa-undo me-1"), "Reset"],
                                            id="reset-btn",
                                            color="secondary",
                                            outline=True,
                                            size="sm"
                                        ),
                                        dbc.Button(
                                            [html.I(className="fas fa-download me-1"), "Export"],
                                            id="export-btn",
                                            color="info",
                                            outline=True,
                                            size="sm"
                                        )
                                    ], className="w-100")
                                ])
                            ], className="shadow-sm sticky-top", style={"top": "20px"})
                        ], width=3),

                        # Right content area - Visualizations
                        dbc.Col([
                            # Keep loading spinners scoped to individual visuals.
                            # A page-level Loading wrapper causes the entire right
                            # panel (tables + charts) to show a loader even when we
                            # only update the map viewport.
                            dbc.Tabs([
                                        # Tab 1: Overview
                                        dbc.Tab([
                                            dbc.Card([
                                                dbc.CardBody([
                                                    dcc.Loading(
                                                        id="loading-overview-map",
                                                        type="default",
                                                        children=[
                                                            dcc.Graph(
                                                                id='overview-map',
                                                                figure=create_initial_map(),
                                                                config={'displayModeBar': True,
                                                                        'displaylogo': False}
                                                            )
                                                        ]
                                                    )
                                                ])
                                            ], className="shadow-sm border-0 mb-3"),

                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Card([
                                                        dbc.CardBody([
                                                            html.H5("Site Rankings",
                                                                    className="mb-3"),
                                                            html.Div(id='site-rankings-table')
                                                        ])
                                                    ], className="shadow-sm border-0")
                                                ])
                                            ])
                                        ], label="Optimal Sites",
                                            tab_id="tab-overview",
                                            label_style={"font-weight": "bold"}),

                                        # Tab 3: Analytics
                                        dbc.Tab([
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Card([
                                                        dbc.CardBody([
                                                            dcc.Graph(id='score-distribution')
                                                        ])
                                                    ], className="shadow-sm border-0 mb-3")
                                                ], md=6),
                                                dbc.Col([
                                                    dbc.Card([
                                                        dbc.CardBody([
                                                            dcc.Graph(id='radar-comparison')
                                                        ])
                                                    ], className="shadow-sm border-0 mb-3")
                                                ], md=6)
                                            ]),
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Card([
                                                        dbc.CardBody([
                                                            dcc.Graph(id='component-comparison')
                                                        ])
                                                    ], className="shadow-sm border-0")
                                                ])
                                            ])
                                        ], label="Analytics", tab_id="tab-analytics"),
                                        
                                        dbc.Tab([
                                            dbc.Card([
                                                dbc.CardBody([
                                                    html.H4("Methodology Overview", className="mb-3"),
                                                    html.P([
                                                        "This tool implements a multi-criteria decision analysis (MCDA) ",
                                                        "framework to identify optimal locations for electric truck charging ",
                                                        "infrastructure in Massachusetts. The analysis integrates different variables ",
                                                        "across census tracts, combining demand patterns, infrastructure capacity, ",
                                                        "accessibility metrics, and equity considerations."
                                                    ], className="lead"),

                                                    html.Hr(),

                                                    html.H5("Scoring Components", className="mt-4 mb-3"),

                                                    # Demand Component
                                                    html.Div([
                                                        html.H6([
                                                            dbc.Badge("40%", color="primary", className="me-2"),
                                                            "Demand"
                                                        ], className="mb-2"),
                                                        html.Ul([
                                                            html.Li([
                                                                html.Strong("LOCUS Trip Data: "),
                                                                "Trip ends by purpose, weekday/weekend, equity community and time of day"
                                                            ]),
                                                            # html.Li([
                                                            #     html.Strong("Domiciled Vehicles: "),
                                                            #     "Heavy and medium-duty trucks domiciled per tract (direct tract-level data from LOCUS). ",
                                                            #     "Includes both total domiciled vehicles and percentage of local stops from domiciled vehicles."
                                                            # ]),
                                                            # html.Li([
                                                            #     html.Strong("Stop Duration/Air Quality Improvement Potential Filtering: "),
                                                            #     "Only trip ends with stops ≥ 30 minutes are considered viable charging opportunities. ",
                                                            #     "Stop duration is now 25% of the demand score, combining average stop time and % of eligible trips."
                                                            # ]),
                                                            html.Li([
                                                                html.Strong("Traffic Volume: "),
                                                                "AADT-based heavy truck traffic from MassDOT"
                                                            ]),
                                                            
                                                            html.Li([
                                                                html.Strong("Temporal Demand Patterns: "),
                                                                "Temporal stability (uniformity of demand throughout day) and peak intensity (how pronounced peaks are). ",
                                                                "Stable demand = suitable for depot/overnight charging. Peaky demand = need for fast charging infrastructure. ",
                                                                "Calculated using coefficient of variation, peak-to-average ratio, and entropy measures from time-of-day trip data."
                                                            ])
                                                        ], className="small mb-3")
                                                    ], className="mb-3"),
                                                    
                                                    
                                                    # html.H5("Charging Type Classification", className="mt-4 mb-3"),
                                                    # html.P([
                                                    #     "After scoring, each feasible site is classified into one of three charging facility types ",
                                                    #     "based on demand patterns and operational characteristics. This classification helps ",
                                                    #     "match infrastructure requirements to actual usage patterns."
                                                    # ], className="mb-3"),

                                                    # dbc.Row([
                                                    #     dbc.Col([
                                                    #         dbc.Card([
                                                    #             dbc.CardHeader("Classification Criteria", className="bg-primary text-white"),
                                                    #             dbc.CardBody([
                                                    #                 html.Div([
                                                    #                     html.H6("Depot/Overnight", className="text-primary mb-2"),
                                                    #                     html.Ul([
                                                    #                         html.Li([html.Strong("Domiciled trucks: "), "> 20 per tract"], className="small"),
                                                    #                         html.Li([html.Strong("Domicile ratio: "), "> 60% of total truck activity"], className="small"),
                                                    #                         html.Li([html.Strong("Evening activity: "), "> 25% of trips 7pm-6am"], className="small"),
                                                    #                         html.Li([html.Strong("Use case: "), "Fleet return-to-base charging"], className="small")
                                                    #                     ], className="mb-3"),
                                                                        
                                                    #                     html.H6("Opportunistic/Top-Up", className="text-warning mb-2"),
                                                    #                     html.Ul([
                                                    #                         html.Li([html.Strong("Stop duration: "), "30-120 minutes average"], className="small"),
                                                    #                         html.Li([html.Strong("Trip ends: "), "> 50 charging-eligible stops"], className="small"),
                                                    #                         html.Li([html.Strong("Daytime activity: "), "> 40% during 10am-7pm"], className="small"),
                                                    #                         html.Li([html.Strong("Use case: "), "Delivery routes, local operations"], className="small")
                                                    #                     ], className="mb-3"),
                                                                        
                                                    #                     html.H6("En-Route/Corridor", className="text-success mb-2"),
                                                    #                     html.Ul([
                                                    #                         html.Li([html.Strong("AADT: "), "> 500 heavy trucks/day"], className="small"),
                                                    #                         html.Li([html.Strong("Long-haul %: "), "> 50% of trips"], className="small"),
                                                    #                         html.Li([html.Strong("Highway access: "), "Interstate proximity"], className="small"),
                                                    #                         html.Li([html.Strong("Use case: "), "Long-distance freight corridors"], className="small")
                                                    #                     ], className="mb-0")
                                                    #                 ])
                                                    #             ])
                                                    #         ], className="h-100")
                                                    #     ], md=6),
                                                        
                                                    #     dbc.Col([
                                                    #         dbc.Card([
                                                    #             dbc.CardHeader("Infrastructure Requirements", className="bg-success text-white"),
                                                    #             dbc.CardBody([
                                                    #                 html.Table([
                                                    #                     html.Thead([
                                                    #                         html.Tr([
                                                    #                             html.Th("Type", className="small"),
                                                    #                             html.Th("Power Level", className="small"),
                                                    #                             html.Th("Dwell Time", className="small"),
                                                    #                             html.Th("Chargers/Site", className="small")
                                                    #                         ])
                                                    #                     ]),
                                                    #                     html.Tbody([
                                                    #                         html.Tr([
                                                    #                             html.Td("Depot", className="small"),
                                                    #                             html.Td("7-19 kW (L2)", className="small"),
                                                    #                             html.Td("8+ hours", className="small"),
                                                    #                             html.Td("10-50", className="small")
                                                    #                         ]),
                                                    #                         html.Tr([
                                                    #                             html.Td("Opportunistic", className="small"),
                                                    #                             html.Td("50-150 kW (DC)", className="small"),
                                                    #                             html.Td("30-120 min", className="small"),
                                                    #                             html.Td("4-10", className="small")
                                                    #                         ]),
                                                    #                         html.Tr([
                                                    #                             html.Td("Corridor", className="small"),
                                                    #                             html.Td("150-350+ kW", className="small"),
                                                    #                             html.Td("<30 min", className="small"),
                                                    #                             html.Td("4-8", className="small")
                                                    #                         ])
                                                    #                     ])
                                                    #                 ], className="table table-sm table-striped mb-0")
                                                    #             ])
                                                    #         ], className="h-100")
                                                    #     ], md=6)
                                                    # ], className="mb-4"),

                                                    # html.P([
                                                    #     html.Strong("Mixed Type Sites: "),
                                                    #     "Some locations qualify for multiple charging types based on diverse demand patterns. ",
                                                    #     "These sites may benefit from hybrid infrastructure supporting different use cases."
                                                    # ], className="small text-muted"),
                                                    

                                                    # Infrastructure Component
                                                    html.Div([
                                                        html.H6([
                                                            dbc.Badge("25%", color="success", className="me-2"),
                                                            "Infrastructure"
                                                        ], className="mb-2"),
                                                        html.Ul([
                                                            # html.Li([
                                                            #     html.Strong("Electric Grid Infrastructure (40%): "),
                                                            #     html.Div([
                                                            #         html.Ul([
                                                            #             html.Li([
                                                            #                 html.Strong("E3 Substations: "),
                                                            #                 "Number and density of substations directly in census tract, feeder headroom capacity (MVA)"
                                                            #             ]),
                                                            #             html.Li([
                                                            #                 html.Strong("National Grid: "),
                                                            #                 "Available capacity within 5 miles, renewable integration (solar/wind/storage), grid utilization metrics"
                                                            #             ]),
                                                            #             html.Li([
                                                            #                 html.Strong("EV Readiness: "),
                                                            #                 "Parcel-level suitability, solar potential (kW), existing infrastructure"
                                                            #             ])
                                                            #         ], className="small", style={'marginLeft': '20px', 'marginTop': '5px'})
                                                            #     ])
                                                            # ]),
                                                            html.Li([
                                                                html.Strong("Existing Truck Charger Gaps (45%): "),
                                                                "Distance to existing Light-duty charging infrastructure"
                                                            ]),
                                                            # html.Li([
                                                            #     html.Strong("Warehouse & Logistics (12%): "),
                                                            #     "Proximity to warehouses and freight facilities within 5 miles"
                                                            # ]),
                                                            # html.Li([
                                                            #     html.Strong("Co-location Opportunities (12%): "),
                                                            #     "Retail/commercial POIs, rest stops, gas stations, hotels for public charging"
                                                            # ]),
                                                            # html.Li([
                                                            #     html.Strong("Expansion Potential (8%): "),
                                                            #     "Available parking area for charging infrastructure expansion"
                                                            # ]),
                                                            html.Li([
                                                                html.Strong("Co-location with Transit & Transit Parking Lots (30%): "),
                                                                "Parking capacity at transit facilities within 5 miles"
                                                            ]),
                                                            html.Li([
                                                                html.Strong("Co-location with government & social services (25%):"),
                                                                "Government spaces within 5 miles"
                                                            ])
                                                        ], className="small mb-3")
                                                    ], className="mb-3"),

                                                    # Accessibility Component
                                                    html.Div([
                                                        html.H6([
                                                            dbc.Badge("20%", color="warning", className="me-2"),
                                                            "Accessibility"
                                                        ], className="mb-2"),
                                                        html.Ul([
                                                            # html.Li([
                                                            #     html.Strong("Interstate & NHS Routes: "),
                                                            #     "Binary flags for Interstate highways and National Highway System"
                                                            # ]),
                                                            # html.Li([
                                                            #     html.Strong("Freight Corridors: "),
                                                            #     "Designated truck routes, multi-lane segments, corridor density"
                                                            # ]),
                                                            html.Li([
                                                                html.Strong("Network Density: "),
                                                                "Auto-oriented facility miles per square mile (EPA SLD)"
                                                            ]),
                                                            html.Li([
                                                                html.Strong("Co-location with grocery stores: "),
                                                                "Grocery stores within 5 miles"
                                                            ]),
                                                            html.Li([
                                                                html.Strong("Co-location with gas stations: "),
                                                                "Gas stations within 5 miles"
                                                            ])
                                                        ], className="small mb-3")
                                                    ], className="mb-3"),

                                                    # Equity & Environmental Component
                                                    html.Div([
                                                        html.H6([
                                                            dbc.Badge("15%", color="info", className="me-2"),
                                                            "Equity & Environmental"
                                                        ], className="mb-2"),
                                                        html.Ul([
                                                            html.Li([
                                                                html.Strong("Environmental Justice: "),
                                                                "EJ block group designations (income, minority, English isolation criteria)"
                                                            ]),
                                                            html.Li([
                                                                html.Strong("Land Use Suitability: "),
                                                                "Commercial (1.0), Industrial (0.9), Transportation (1.0) weighted scores from MA_LCLU2016"
                                                            ]),
                                                            html.Li([
                                                                html.Strong("POI Constraints: "),
                                                                "Buffer distances from schools, hospitals, and places of worship (exclusion zones)"
                                                            ]),
                                                            html.Li([
                                                                html.Strong("Parcel Viability: "),
                                                                "Commercial/industrial zoning, sufficient parcel size, protected land exclusions"
                                                            ])
                                                        ], className="small mb-3")
                                                    ], className="mb-3"),

                                                    html.Hr(),

                                                    html.H5("Data Sources & Processing", className="mt-4 mb-3"),

                                                    dbc.Accordion([
                                                        dbc.AccordionItem([
                                                            html.P([
                                                                html.Strong("Source: "),
                                                                "LOCUS person trip modeling data"
                                                            ], className="mb-2"),
                                                            html.Ul([
                                                                html.Li("Daily trips by purpose (home, regular, other)"),
                                                                html.Li("Daily trips by weekday/weekend"),
                                                                html.Li("Daily trips by equity community"),
                                                                html.Li("Daily trips by time of day"),
                                                                html.Li("Aggregated to census tract level")
                                                            ], className="small mb-0")
                                                        ], title="LOCUS Trip Data"),

                                                        dbc.AccordionItem([
                                                            html.P([
                                                                html.Strong("Source: "),
                                                                "National Grid Massachusetts System Data Portal"
                                                            ], className="mb-2"),
                                                            html.Ul([
                                                                html.Li("375 substation point locations with coordinates"),
                                                                html.Li("960 three-phase feeder records with capacity data"),
                                                                html.Li("2027 load forecasts (MVA) and peak utilization percentages"),
                                                                html.Li("Connected and pending renewable generation (MW)"),
                                                                html.Li("Spatial aggregation: 5-mile buffer from tract centroids")
                                                            ], className="small"),
                                                            html.P([
                                                                html.Strong("Calculation: "),
                                                                html.Code("Available Capacity = Forecasted Load × (100 - Peak Utilization%) / 100")
                                                            ], className="small text-muted mb-0")
                                                        ], title="National Grid Infrastructure"),

                                                        dbc.AccordionItem([
                                                            html.P([
                                                                html.Strong("Source: "),
                                                                "MA_LCLU2016.gdb (MassGIS Land Cover/Land Use 2016)"
                                                            ], className="mb-2"),
                                                            html.Ul([
                                                                html.Li("22+ million parcel-level polygons"),
                                                                html.Li("Categorized into 10 classes: commercial, industrial, transportation, residential, public/institutional, recreation, protected/natural, agriculture, vacant, other"),
                                                                html.Li("Spatial intersection with census tracts"),
                                                                html.Li("Area calculations and percentage-based suitability scores")
                                                            ], className="small mb-0")
                                                        ], title="Land Use/Land Cover"),

                                                        dbc.AccordionItem([
                                                            html.P([
                                                                html.Strong("Source: "),
                                                                "MassDOT Traffic Volume and Classification"
                                                            ], className="mb-2"),
                                                            html.Ul([
                                                                html.Li("Annual Average Daily Traffic (AADT) by road segment"),
                                                                html.Li("Truck percentage and heavy truck classification"),
                                                                html.Li("National Highway System (NHS) route designations"),
                                                                html.Li("Interstate highway flags"),
                                                                html.Li("Length-weighted aggregation to tract level")
                                                            ], className="small mb-0")
                                                        ], title="Traffic Data (AADT)"),
                                                        
                                                        
                                                        dbc.AccordionItem([
                                                            html.P([
                                                                html.Strong("Source: "),
                                                                "MassDOT Traffic Volume and Classification"
                                                            ], className="mb-2"),
                                                            
                                                            html.H6("The Double-Counting Problem", className="text-danger mt-3 mb-2"),
                                                            html.P([
                                                                "Traditional GIS approaches sum AADT values from all road segments within a tract. ",
                                                                "However, this creates a critical error: ",
                                                                html.Strong("the same vehicle traveling through multiple connected segments gets counted multiple times.")
                                                            ], className="small mb-2"),
                                                            
                                                            html.P([
                                                                "Example: A truck traveling segments A → B → C on I-90 would be counted 3 times ",
                                                                "if we simply sum AADTs, inflating demand estimates by 200-300%."
                                                            ], className="small text-muted fst-italic mb-3"),
                                                            
                                                            html.H6("Our Solution: Path-Based AADT Analysis", className="text-success mt-3 mb-2"),
                                                            html.P([
                                                                "We implement a network-based approach that traces vehicle paths through connected ",
                                                                "road segments, counting each unique vehicle flow only once."
                                                            ], className="small mb-2"),
                                                            
                                                            html.Strong("Methodology:", className="small d-block mb-2"),
                                                            html.Ol([
                                                                html.Li([
                                                                    html.Strong("Build Directed Network: "),
                                                                    "Create a graph where road segments are edges with direction (northbound vs southbound)"
                                                                ], className="small mb-1"),
                                                                html.Li([
                                                                    html.Strong("Trace Consistent Paths: "),
                                                                    "Follow connected segments where AADT values are consistent (within 20% tolerance), ",
                                                                    "indicating the same vehicles continuing on the route"
                                                                ], className="small mb-1"),
                                                                html.Li([
                                                                    html.Strong("Apply Constraints: "),
                                                                    "Stop path tracing when: (a) AADT changes >20% (vehicles entering/exiting), ",
                                                                    "(b) path exceeds 50 miles, or (c) connectivity breaks"
                                                                ], className="small mb-1"),
                                                                html.Li([
                                                                    html.Strong("Count Unique Vehicles: "),
                                                                    "Each traced path represents a unique vehicle flow. AADT is counted once per path, ",
                                                                    "not once per segment"
                                                                ], className="small mb-1")
                                                            ], className="mb-3"),
                                                            
                                                            
                                                            html.H6("Two Metrics: Segment vs Path", className="mb-2"),
                                                            html.P([
                                                                "We generate ", html.Strong("two complementary sets of metrics:"),
                                                            ], className="small mb-2"),
                                                            
                                                            dbc.Row([
                                                                dbc.Col([
                                                                    dbc.Card([
                                                                        dbc.CardBody([
                                                                            html.H6("Segment-Based Metrics", className="text-primary mb-2"),
                                                                            html.P("Measures exposure and activity", className="small text-muted mb-2"),
                                                                            html.Ul([
                                                                                html.Li("total_road_miles", className="small font-monospace"),
                                                                                html.Li("avg_aadt_weighted", className="small font-monospace"),
                                                                                html.Li("unique_trucks_daily", className="small font-monospace"),
                                                                                html.Li("unique_heavy_trucks_daily", className="small font-monospace"),
                                                                                html.Li("truck_density", className="small font-monospace"),
                                                                                html.Li("traffic_volume_miles", className="small font-monospace")
                                                                            ], className="mb-2"),
                                                                            html.P([
                                                                                html.Strong("Use for: "),
                                                                                "Road network density, infrastructure exposure, accessibility scoring"
                                                                            ], className="small text-info mb-0")
                                                                        ], className="p-2")
                                                                    ], className="border-primary border-2 h-100")
                                                                ], md=6),
                                                                
                                                                dbc.Col([
                                                                    dbc.Card([
                                                                        dbc.CardBody([
                                                                            html.H6("Path-Based Metrics", className="text-success mb-2"),
                                                                            html.P("Measures unique vehicle demand", className="small text-muted mb-2"),
                                                                            html.Ul([
                                                                                html.Li("unique_vehicles_daily", className="small font-monospace"),
                                                                                html.Li("unique_trucks_daily", className="small font-monospace"),
                                                                                html.Li("unique_heavy_trucks_daily", className="small font-monospace"),
                                                                                html.Li("num_distinct_paths", className="small font-monospace"),
                                                                                html.Li("total_path_miles", className="small font-monospace"),
                                                                                html.Li("traffic_inflation_ratio", className="small font-monospace")
                                                                            ], className="mb-2"),
                                                                            html.P([
                                                                                html.Strong("Use for: "),
                                                                                "Charging demand estimation, unique vehicle counts (no double-counting)"
                                                                            ], className="small text-success mb-0")
                                                                        ], className="p-2")
                                                                    ], className="border-success border-2 h-100")
                                                                ], md=6)
                                                            ], className="mb-3"),
                                                            
                                                            
                                                            html.H6("Traffic Inflation Ratio", className="mb-2"),
                                                            html.P([
                                                                "The ", html.Code("traffic_inflation_ratio"), " shows how much the naive segment-based ",
                                                                "approach overestimates vehicle counts compared to the path-based approach:"
                                                            ], className="small mb-2"),
                                                            
                                                            html.Ul([
                                                                html.Li([
                                                                    html.Strong("Ratio = 1.0: "),
                                                                    "No double-counting (simple road network)"
                                                                ], className="small"),
                                                                html.Li([
                                                                    html.Strong("Ratio = 2.5: "),
                                                                    "Segment-based count is 2.5× higher (250% inflation)"
                                                                ], className="small"),
                                                                html.Li([
                                                                    html.Strong("Ratio > 3.0: "),
                                                                    "Severe double-counting in complex interchange areas"
                                                                ], className="small")
                                                            ], className="mb-3"),
                                                            
                                                            html.Div([
                                                                dbc.Alert([
                                                                    html.I(className="fas fa-lightbulb me-2"),
                                                                    html.Strong("Key Takeaway: "),
                                                                    "For charging infrastructure demand, ALWAYS use ",
                                                                    html.Code("unique_trucks_daily"), " and ", html.Code("unique_heavy_trucks_daily"), 
                                                                    " from path-based analysis. These represent actual unique vehicles that need charging, ",
                                                                    "not inflated counts from double-counting road segments."
                                                                ], color="success", className="mb-0")
                                                            ])
                                                        ], title="AADT Traffic Analysis (Path-Based Methodology)"),

                                                        dbc.AccordionItem([
                                                            html.P([
                                                                html.Strong("Source: "),
                                                                "MassGIS Environmental Justice Populations (2020 Census)"
                                                            ], className="mb-2"),
                                                            html.Ul([
                                                                html.Li("Block group-level EJ designations"),
                                                                html.Li("Income criteria: Median household income ≤ 65% state median"),
                                                                html.Li("Minority criteria: ≥ 40% minority residents"),
                                                                html.Li("English isolation criteria: ≥ 25% limited English proficiency"),
                                                                html.Li("Population-weighted percentages aggregated to tract level")
                                                            ], className="small mb-0")
                                                        ], title="Environmental Justice Data"),

                                                        dbc.AccordionItem([
                                                            html.P([
                                                                html.Strong("Sources: "),
                                                                "EPA Smart Location Database (SLD) Version 3.0"
                                                            ], className="mb-2"),
                                                            html.Ul([
                                                                html.Li("D1A: Gross residential density (HU/acre)"),
                                                                html.Li("D1B: Gross population density (people/acre)"),
                                                                html.Li("D1C: Gross employment density (jobs/acre)"),
                                                                html.Li("D3AAO: Network density (auto-oriented links, miles/sq mi)"),
                                                                html.Li("D4E: Transit service frequency per capita"),
                                                                html.Li("D5AR: Jobs within 45 min auto travel (time-decay weighted)"),
                                                                html.Li("D5BR: Jobs within 45 min transit (distance-decay weighted)")
                                                            ], className="small mb-0")
                                                        ], title="Urban Form & Accessibility"),

                                                        dbc.AccordionItem([
                                                            html.P([
                                                                html.Strong("Sources: "),
                                                                "OpenStreetMap, MassDOT, Alternative Fuels Data Center"
                                                            ], className="mb-2"),
                                                            html.Ul([
                                                                html.Li("POI categories: Schools, hospitals, places of worship, warehouses, gas stations, hotels, parks, colleges, grocery stores"),
                                                                html.Li("Existing EV charging stations (AFDC)"),
                                                                html.Li("Co-location with transit & transit parking lots with parking space counts"),
                                                                html.Li("Intermodal rail facilities (TOFC/COFC)"),
                                                                html.Li("5-mile buffer count aggregation")
                                                            ], className="small mb-0")
                                                        ], title="Points of Interest & Infrastructure")
                                                        
                                                        
                                                        
                                                    ], start_collapsed=True, className="mb-4"),

                                                    html.Hr(),

                                                    html.H5("Spatial Methodology", className="mt-4 mb-3"),
                                                    html.P([
                                                        "All spatial analyses use the Massachusetts State Plane projection (EPSG:26986) ",
                                                        "for accurate distance calculations. The 5-mile buffer radius (8,046.7 meters) ",
                                                        "is applied consistently across all 'within 5 miles' metrics using tract centroids ",
                                                        "or boundaries as origin points."
                                                    ], className="small")
                                                ])
                                            ], className="shadow-sm border-0")
                                        ], label="Documentation", tab_id="tab-docs")
                                    ], id="inner-tabs", active_tab="tab-overview")
                        ], width=9)
                    ])
                ], label="Analysis Dashboard", tab_id="tab-analysis", label_style={"font-weight": "bold"})

            ], id="outer-tabs", active_tab="tab-home")
        ], fluid=True, className="px-4"),

        # Data stores
        dcc.Store(id='scored-data-store'),
        dcc.Store(id='selected-sites-store'),
        dcc.Store(id='config-store'),
        dcc.Download(id='download-export')

    ], style={"backgroundColor": "#f8f9fa", "minHeight": "100vh"})