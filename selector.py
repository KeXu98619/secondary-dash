import geopandas as gpd
import pandas as pd
import numpy as np

class TruckChargingSiteSelector:
    """
    Multi-criteria scoring model for optimal truck charging site selection.
    Updated for Massachusetts data structure with LOCUS, land use, traffic data, and TEMPORAL DEMAND.
    """

    def __init__(self, geojson_path, config=None):
        """
        Initialize the selector with tract-level GeoJSON data.
        """
        self.gdf = gpd.read_file(geojson_path)
        
        # Convert to WGS84 if not already (required for web mapping)
        if self.gdf.crs is not None and self.gdf.crs != 'EPSG:4326':
            print(f"Converting CRS from {self.gdf.crs} to EPSG:4326 for web mapping...")
            self.gdf = self.gdf.to_crs('EPSG:4326')
        elif self.gdf.crs is None:
            print("Warning: No CRS defined. Assuming EPSG:4326...")
            self.gdf.set_crs('EPSG:4326', inplace=True)
        
        self.config = config or self._default_config()
        self.scores = None
        
        self._verify_data_structure()
        
        self._calculate_truck_charger_proximity()
        

    def _verify_data_structure(self):
        """Verify that required columns exist in the data"""
        required_base = ['GEOID', 'geometry']
        missing = [col for col in required_base if col not in self.gdf.columns]

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Log what data is available
        print(f"Loaded {len(self.gdf)} tracts")
        print(f"Available columns: {len(self.gdf.columns)}")

        # Check for key data categories
        has_locus = any('Heavy_Duty' in col or 'Medium_Duty' in col or 'Light_Duty' in col
                        for col in self.gdf.columns)
        has_landuse = any('landuse_pct' in col for col in self.gdf.columns)
        has_traffic = ('unique_heavy_trucks_daily' in self.gdf.columns) or ('total_daily_heavy_trucks' in self.gdf.columns)
        has_domicile = 'domiciled_trucks_tract' in self.gdf.columns
        has_temporal = 'heavy_duty_temporal_cv' in self.gdf.columns  # NEW

        print(f"  LOCUS trip data: {'✓' if has_locus else '✗'}")
        print(f"  Land use data: {'✓' if has_landuse else '✗'}")
        print(f"  Traffic (AADT) data: {'✓' if has_traffic else '✗'}")
        print(f"  Domiciled trucks data: {'✓' if has_domicile else '✗'}")
        print(f"  Temporal demand data: {'✓' if has_temporal else '✗'}")  # NEW

    def _default_config(self):
        """Default configuration for scoring weights and constraints."""
        return {
            'weights': {
                'demand': 0.40,
                'infrastructure': 0.25,
                'accessibility': 0.20,
                'equity_feasibility': 0.15
            },
            'constraints': {
                # Person-trip based feasibility
                'min_person_trips': 10,

                # Optional: when enabled, remove tracts outside the 0.5-mi secondary-network buffer
                'only_within_secondary_buffer': True,

                # Optional: when enabled, keep only rural tracts (rural_flag == 1)
                'only_rural': False,

                # Optional: when enabled, remove tracts with 0 feeder headroom from feasibility
                'exclude_zero_headroom': False,

                # Kept for backward compatibility / other scoring modules (may be unused)
                'min_ev_charging_dist_mi': 0,
                'min_commercial_pct': 5,
                'max_protected_pct': 50,
            },
            'demand_weights': {
                # Trip purpose weights (sum to 100 within this group)
                'home_end_weight': 40,
                'workplace_end_weight': 40,
                'other_end_weight': 20,

                # Day-of-week weights (sum to 100 within this group)
                'weekday_weight': 70,
                'weekend_weight': 30,

                # Equity community weights (sum to 100 within this group)
                'equity_community_weight': 50,
                'non_equity_community_weight': 50,

                # Temporal pattern weights (sum to 100 within this group)
                'temporal_stability_weight': 60,
                'temporal_peak_weight': 40,
            },
            # Sub-component weights within demand (must sum to 1.0)
            'demand_component_weights': {
                'purpose': 0.35,
                'day_of_week': 0.25,
                'equity_trips': 0.20,
                'temporal_pattern': 0.20,
            },

            # ===== ADD THESE: =====
            
            # Infrastructure sub-weights (normalized in calculation)
            'infrastructure_weights': {
                    # Only the requested subfactors
                    'truck_charger_gap_weight': 0.45,
                    'park_ride_weight': 0.30,
                    'government_weight': 0.25
                },
            
            # Accessibility sub-weights (must sum to 1.0)
            'accessibility_weights': {
                'network_weight': 0.50,
                'grocery_weight': 0.25,
                'gas_station_weight': 0.25
            },
            
            # Equity sub-weights (normalized in calculation)
            'equity_weights': {
                    'ej_priority_weight': 0.40,
                    'landuse_suit_weight': 0.35,
                    'commercial_industrial_weight': 0.15,
                    'protected_penalty_weight': 0.10
                },
            
            # Analysis mode flags
            'secondary_corridor_mode': False,
            'fleet_hub_mode': False,
}



    def apply_minimal_constraints(self):
        """
        Apply only critical hard constraints (absolute deal-breakers).
        These apply regardless of scoring weights and are minimal barriers.
        
        The goal: Let scoring determine feasibility, not hard filters.
        """
        df = self.gdf.copy()
        feasible = pd.Series(True, index=df.index)
        constraints = self.config['constraints']
        min_person = constraints.get('min_person_trips', 10)
        
        print("  Applying minimal constraints:")
        
        # Constraint 1: Must have SOME person trip activity (very relaxed)

        # Use total person trips = equity_0_trips + equity_1_trips
        person_trips = pd.Series(0, index=df.index)
        if 'equity_0_trips' in df.columns:
            person_trips += df['equity_0_trips'].fillna(0)
        if 'equity_1_trips' in df.columns:
            person_trips += df['equity_1_trips'].fillna(0)

        # Absolute minimal bar: at least 10 person trip (no hard-coded % of user threshold)
        if person_trips.max() > 0:
            feasible &= person_trips >= min_person
            print(f"    Person trips ≥ 10: {feasible.sum()} tracts pass")


        # Constraint 1.5 (optional): Only include rural tracts
        # Controlled by UI toggle "Only include rural tracts".
        # Preferred column is `rural_flag` (1=rural, 0=not rural), but we fall back
        # to a few common schemas if needed.
        if constraints.get('only_rural', False):
            rural_mask = None

            if 'rural_flag' in df.columns:
                # Handle numeric, boolean, and string representations robustly
                rf = df['rural_flag']
                rf_num = pd.to_numeric(rf, errors='coerce')
                rural_mask = (rf_num.fillna(0).astype(float) >= 1)
            elif 'is_rural' in df.columns:
                rural_mask = df['is_rural'].fillna(False).astype(bool)
            elif 'rural' in df.columns:
                rural_mask = df['rural'].fillna(False).astype(bool)
            elif 'urban_rural_context' in df.columns:
                rural_mask = df['urban_rural_context'].fillna('').astype(str).str.lower().eq('rural')

            if rural_mask is not None:
                feasible &= rural_mask
                print(f"    Rural-only filter enabled: {feasible.sum()} tracts pass")
            else:
                print("    Rural-only filter enabled, but no rural flag column found (expected `rural_flag`)")


        # Constraint 2: Not almost entirely protected land
        if 'landuse_pct_protected_natural' in df.columns:
            feasible &= df['landuse_pct_protected_natural'] < 95
            print(f"    Protected land < 95%: {feasible.sum()} tracts pass")
        elif 'mostly_protected' in df.columns:
            feasible &= df['mostly_protected'] == 0
            print(f"    Not mostly protected: {feasible.sum()} tracts pass")
        

        # Constraint 2.5 (optional): Exclude tracts with 0 feeder headroom (grid constraint)
        # Only applies when UI toggle 'Exclude tracts with 0 feeder headroom' is ON.
        if constraints.get('exclude_zero_headroom', False):
            if 'median_feeder_headroom_mva' in df.columns:
                headroom = df['median_feeder_headroom_mva'].fillna(0)
                feasible &= headroom > 0
                print(f"    Grid headroom > 0 MVA: {feasible.sum()} tracts pass (excluded {(headroom <= 0).sum()} tracts)")
            else:
                print("    Grid headroom constraint enabled, but median_feeder_headroom_mva column not found")
        # Constraint 3: Has SOME development potential (very relaxed)
        if 'truck_feasibility_tier' in df.columns:
            # Accept tier 0 if it has ANY commercial/industrial land
            has_potential = (
                (df['truck_feasibility_tier'] >= 0) |  # Any tier
                (df.get('landuse_pct_commercial', 0) > 0.5) |  # >0.5% commercial
                (df.get('landuse_pct_industrial', 0) > 0.5) |  # >0.5% industrial
                (df.get('truck_suitability_final', 0) > 10)  # Or suitability > 10
            )
            feasible &= has_potential
            print(f"    Has development potential: {feasible.sum()} tracts pass")
        elif 'truck_suitability_final' in df.columns:
            feasible &= df['truck_suitability_final'] >= 10  # Very low bar
            print(f"    Suitability ≥ 10: {feasible.sum()} tracts pass")
        
        # Constraint 4: Not over-saturated with chargers (relaxed)
        if 'ev_charging_stations_within_5mi' in df.columns:
            # feasible &= df['ev_charging_stations_within_5mi'] < 100  # Very high threshold  # DISABLED per client request
            print(f"    Not over-saturated (< 100 chargers): {feasible.sum()} tracts pass")
        
        print(f"  → TOTAL passing minimal constraints: {feasible.sum()} / {len(feasible)} tracts ({feasible.sum()/len(feasible)*100:.1f}%)\n")
        
        return feasible
    
    
    def calculate_demand_score(self):
        """
        Calculate demand score (40% of total).
        Based on LOCUS trip data, AADT traffic, domiciled vehicles, stop duration, AND TEMPORAL PATTERNS.
        """
        df = self.gdf.copy()
        
        # IMPORTANT:
        # "demand_weights" contains multiple *separate* subfactor groups
        # (vehicle class, trip type, stop-duration, temporal, etc.).
        # Normalizing the entire dict as one pool will unintentionally shrink each
        # group's weights and depress the demand score.
        #
        # Therefore:
        #   - We normalize component_weights (since those are a single group)
        #   - We normalize demand subfactor weights *within each group* right before use
        demand_weights = self.config.get('demand_weights', {})
        component_weights = self._normalize_weight_dict(self.config.get('demand_component_weights', {}))
        
        demand_components = []
        # Component 1: Trip purpose
        if all(col in df.columns for col in ['purpose_1_trips', 'purpose_2_trips', 'purpose_3_trips']):
            home_score = self._normalize_score_with_density(df.get('purpose_1_trips', 0), use_density=True)
            work_score = self._normalize_score_with_density(df.get('purpose_2_trips', 0), use_density=True)
            other_score = self._normalize_score_with_density(df.get('purpose_3_trips', 0), use_density=True)

            if self._is_group_disabled(demand_weights, ['home_end_weight', 'workplace_end_weight', 'other_end_weight']):
                print('  Trip purpose weights set to 0 → skipping purpose component')
            else:
                w_home, w_work, w_other = self._normalize_weight_group(
                    demand_weights,
                    keys=['home_end_weight', 'workplace_end_weight', 'other_end_weight'],
                    defaults=[0.4, 0.4, 0.2],
                )
                purpose_score = (home_score * w_home + work_score * w_work + other_score * w_other)
                weight = component_weights.get('purpose', 0.35)
                demand_components.append(('purpose', purpose_score, weight))

        # Component 2: Day of week
        if all(col in df.columns for col in ['dow_1_trips', 'dow_2_3_trips']):
            weekday_score = self._normalize_score_with_density(df.get('dow_1_trips', 0), use_density=True)
            weekend_score = self._normalize_score_with_density(df.get('dow_2_3_trips', 0), use_density=True)

            if self._is_group_disabled(demand_weights, ['weekday_weight', 'weekend_weight']):
                print('  Day-of-week weights set to 0 → skipping day_of_week component')
            else:
                w_wd, w_we = self._normalize_weight_group(
                    demand_weights,
                    keys=['weekday_weight', 'weekend_weight'],
                    defaults=[0.7, 0.3],
                )
                dow_score = (weekday_score * w_wd + weekend_score * w_we)
                weight = component_weights.get('day_of_week', 0.25)
                demand_components.append(('day_of_week', dow_score, weight))

        # Component 3: Equity vs non-equity trips
        if all(col in df.columns for col in ['equity_0_trips', 'equity_1_trips']):
            non_equity_score = self._normalize_score_with_density(df.get('equity_0_trips', 0), use_density=True)
            equity_score = self._normalize_score_with_density(df.get('equity_1_trips', 0), use_density=True)

            if self._is_group_disabled(demand_weights, ['equity_community_weight', 'non_equity_community_weight']):
                print('  Equity-trip weights set to 0 → skipping equity_trips component')
            else:
                w_eq, w_non = self._normalize_weight_group(
                    demand_weights,
                    keys=['equity_community_weight', 'non_equity_community_weight'],
                    defaults=[0.5, 0.5],
                )
                equity_trips_score = (equity_score * w_eq + non_equity_score * w_non)
                weight = component_weights.get('equity_trips', 0.20)
                demand_components.append(('equity_trips', equity_trips_score, weight))

        # Component 4: TEMPORAL DEMAND PATTERN (keep existing control logic)
        stability_col = None
        peak_col = None
        if 'passenger_temporal_stability_score' in df.columns and 'passenger_peak_demand_score' in df.columns:
            stability_col = 'passenger_temporal_stability_score'
            peak_col = 'passenger_peak_demand_score'
        elif 'truck_temporal_stability_score' in df.columns and 'truck_peak_demand_score' in df.columns:
            stability_col = 'truck_temporal_stability_score'
            peak_col = 'truck_peak_demand_score'

        if stability_col and peak_col:
            stability_score = df[stability_col]
            peak_score = df[peak_col]
            if self._is_group_disabled(demand_weights, ['temporal_stability_weight', 'temporal_peak_weight']):
                print('  Temporal weights set to 0 → skipping temporal_pattern component')
            else:
                w_stab, w_peak = self._normalize_weight_group(
                    demand_weights,
                    keys=['temporal_stability_weight', 'temporal_peak_weight'],
                    defaults=[0.6, 0.4],
                )
                temporal_score = (stability_score * w_stab + peak_score * w_peak)
                weight = component_weights.get('temporal_pattern', 0.20)
                demand_components.append(('temporal_pattern', temporal_score, weight))
                self.gdf['temporal_component_score'] = temporal_score
        else:
            print('  Warning: Temporal demand metrics not found, skipping temporal component')

        # Combine all available components
        if demand_components:
            total_weight = sum(weight for _, _, weight in demand_components)
            raw_demand = sum(score * (weight / total_weight) 
                            for _, score, weight in demand_components)
            
            print(f"\n  Demand components used: {len(demand_components)}")
            for name, _, weight in demand_components:
                print(f"    - {name}: {weight/total_weight*100:.1f}% of demand score")
        else:
            print("Warning: No demand data available, using zeros")
            raw_demand = pd.Series(0, index=df.index)

        demand_score = raw_demand.clip(0, 100)
        return demand_score

    def calculate_infrastructure_score(self, existing_charging_gdf=None):
        """Calculate infrastructure score.
    
        Per current dashboard design, this score ONLY uses:
          - Ability to fill gaps in charging network (truck charger gap)
          - Co-location with transit & transit parking lots (Park & Ride)
          - Co-location with government spaces
    
        All other infrastructure signals (e.g., grid, retail co-location, expansion)
        are intentionally excluded.
        """
        df = self.gdf.copy()
        scores = pd.Series(0, index=df.index)
    
        # Merge user-provided weights with defaults so missing keys never crash scoring
        _infra_defaults = {
            'truck_charger_gap_weight': 0.45,
            'park_ride_weight': 0.30,
            'government_weight': 0.25,
        }
        infra_weights = {**_infra_defaults, **(self.config.get('infrastructure_weights') or {})}
    
        # Allow users to disable this entire section by setting ALL component weights to 0
        try:
            infra_total = float(sum([float(v or 0) for v in infra_weights.values()]))
        except Exception:
            infra_total = 1.0
        if infra_total == 0:
            print("   Infrastructure component weights set to 0 → infrastructure score disabled")
            return pd.Series(0, index=df.index)
    
        # Normalize in case user provided point-style weights (sum ~100)
        infra_weights = self._normalize_weight_dict(infra_weights)
    
        # ---- Infrastructure scoring debug helpers ----
        def _pct(x: float) -> float:
            return 100.0 * float(x)

        def _dist_stats(name: str, s: pd.Series):
            s_num = pd.to_numeric(s, errors="coerce")
            nan_rate = s_num.isna().mean()
            s_fill = s_num.fillna(0)

            zero_rate = (s_fill == 0).mean()
            arr = s_num.dropna().to_numpy(dtype=float)

            if arr.size == 0:
                stats = {"min": np.nan, "p10": np.nan, "p50": np.nan, "p90": np.nan, "max": np.nan}
            else:
                stats = {
                    "min": float(np.min(arr)),
                    "p10": float(np.percentile(arr, 10)),
                    "p50": float(np.percentile(arr, 50)),
                    "p90": float(np.percentile(arr, 90)),
                    "max": float(np.max(arr)),
                }

            print(f"   {name} raw:")
            print(f"     count={int(s_num.shape[0])}, nan%={_pct(nan_rate):.1f}%, zero% (after fill)={_pct(zero_rate):.1f}%")
            print(f"     min={stats['min']:.3f}, p10={stats['p10']:.3f}, median={stats['p50']:.3f}, p90={stats['p90']:.3f}, max={stats['max']:.3f}")

            return s_num, s_fill, stats

        def _score_stats(name: str, score: pd.Series):
            s = pd.to_numeric(score, errors="coerce").fillna(0)
            zero_rate = (s == 0).mean()
            arr = s.to_numpy(dtype=float)

            print(f"   {name} score:")
            print(f"     zero%={_pct(zero_rate):.1f}%")
            print(f"     min={np.min(arr):.2f}, p10={np.percentile(arr,10):.2f}, median={np.percentile(arr,50):.2f}, p90={np.percentile(arr,90):.2f}, max={np.max(arr):.2f}")

        # ---- Component 1: Truck charger gaps (distance; higher distance = higher "gap" score) ----
        if 'nearest_truck_charger_mi' in df.columns:
            raw_dist, dist_fill, raw_stats = _dist_stats("Truck charger gap distance (mi)", df['nearest_truck_charger_mi'])

            # Use p90 distance as dynamic cap (avoid divide-by-zero)
            p90_dist = raw_stats["p90"]
            cap = p90_dist if (p90_dist is not None and np.isfinite(p90_dist) and p90_dist > 0) else 1.0

            gap_score = 100.0 * (dist_fill.clip(0, cap) / cap)
            gap_score = gap_score.clip(0, 100)

            w = float(infra_weights.get('truck_charger_gap_weight', 0) or 0)
            scores += gap_score * w

            print("   Truck charger gap scoring:")
            print(f"     cap used (p90 distance): {cap:.3f} mi")
            print(f"     weight: {w:.4f}")
            _score_stats("Truck charger gap", gap_score)
            print(f"     median contribution to infra (score * weight): {(gap_score.median() * w):.2f}")

        # ---- Component 2: Park & Ride (5mi buffer) ----
        if 'park_ride_spaces_within_5mi' in df.columns:
            raw_pr, pr_fill, _ = _dist_stats("Park & Ride spaces within 5mi (raw)", df['park_ride_spaces_within_5mi'])

            park_ride_score = self._normalize_score(pr_fill)
            park_ride_score = pd.to_numeric(park_ride_score, errors="coerce").fillna(0).clip(0, 100)

            w = float(infra_weights.get('park_ride_weight', 0) or 0)
            scores += park_ride_score * w

            print("   Park & Ride scoring:")
            print(f"     weight: {w:.4f}")
            _score_stats("Park & Ride", park_ride_score)
            print(f"     median contribution to infra (score * weight): {(park_ride_score.median() * w):.2f}")

        # ---- Component 3: Government spaces (5mi buffer) ----
        if 'government_social_services_within_5mi' in df.columns:
            raw_gov, gov_fill, _ = _dist_stats("Government social services within 5mi (raw)", df['government_social_services_within_5mi'])

            gov_score = self._normalize_score(gov_fill)
            gov_score = pd.to_numeric(gov_score, errors="coerce").fillna(0).clip(0, 100)

            w = float(infra_weights.get('government_weight', 0) or 0)
            scores += gov_score * w

            print("   Government scoring:")
            print(f"     weight: {w:.4f}")
            _score_stats("Government", gov_score)
            print(f"     median contribution to infra (score * weight): {(gov_score.median() * w):.2f}")
            
        infrastructure_score = np.clip(scores, 0, 100)
        return infrastructure_score

    def calculate_accessibility_score(self):
        """Calculate accessibility score (20% of total).

        Per your streamlined subfactor list, Accessibility uses ONLY:
        - Network Density
        - Co-location with grocery stores
        - Co-location with gas stations

        Returns:
            pd.Series of 0-100 accessibility scores.
        """
        df = self.gdf.copy()
        scores = pd.Series(0, index=df.index)

        secondary_corridor_mode = self.config.get('secondary_corridor_mode', False)

        if secondary_corridor_mode:
            # Preserve existing behavior: if the app is run in "secondary corridors only" mode,
            # use the prepared corridor-only accessibility score if present.
            print("   Accessibility scoring mode: SECONDARY CORRIDORS ONLY")
            if 'secondary_corridor_only_score' in df.columns:
                corridor_score = df['secondary_corridor_only_score'].fillna(0)
                scores += corridor_score
                print(f"     Tracts with secondary corridor access: {(corridor_score > 0).sum()}")
        else:
            print("   Accessibility scoring mode: ALL ROAD TYPES")

            access_weights = self.config.get('accessibility_weights', {
                'network_weight': 0.50,
                'grocery_weight': 0.25,
                'gas_station_weight': 0.25
            })

            # Allow users to disable this entire section by setting ALL component weights to 0
            try:
                access_total = float(sum([float(v or 0) for v in access_weights.values()]))
            except Exception:
                access_total = 1.0
            if access_total == 0:
                print("   Accessibility component weights set to 0 → accessibility score disabled")
                return pd.Series(0, index=df.index)

            access_weights = self._normalize_weight_dict(access_weights)

            # Network Density (D3AAO is already a density metric: mi/sq mi) - no conversion
            if 'D3AAO' in df.columns:
                network_score = self._normalize_score(df['D3AAO'])
                scores += network_score * access_weights.get('network_weight', 0)

            # Co-location with grocery stores (prefer 5mi buffer; fallback to in-tract)
            grocery_within = None
            for col in [
                'grocery_stores_within_5mi',
                'grocery_within_5mi',
                'grocery stores within_5mi',
                'grocery_stores within_5mi'
            ]:
                if col in df.columns:
                    grocery_within = col
                    break
            if grocery_within is not None:
                grocery_score = self._normalize_score(df[grocery_within])
                scores += grocery_score * access_weights.get('grocery_weight', 0)
            else:
                grocery_in = None
                for col in ['grocery_stores_in_tract', 'grocery stores in tract', 'grocery_in_tract']:
                    if col in df.columns:
                        grocery_in = col
                        break
                if grocery_in is not None:
                    grocery_score = self._normalize_score_with_density(df[grocery_in], use_density=True)
                    scores += grocery_score * access_weights.get('grocery_weight', 0)

            # Co-location with gas stations (prefer 5mi buffer; fallback to in-tract)
            gas_within = None
            for col in [
                'gas_stations_within_5mi',
                'gas_station_within_5mi',
                'gas stations within_5mi',
                'gas_stations within_5mi'
            ]:
                if col in df.columns:
                    gas_within = col
                    break
            if gas_within is not None:
                gas_score = self._normalize_score(df[gas_within])
                scores += gas_score * access_weights.get('gas_station_weight', 0)
            else:
                gas_in = None
                for col in ['gas_stations_in_tract', 'gas stations in tract', 'gas_station_in_tract']:
                    if col in df.columns:
                        gas_in = col
                        break
                if gas_in is not None:
                    gas_score = self._normalize_score_with_density(df[gas_in], use_density=True)
                    scores += gas_score * access_weights.get('gas_station_weight', 0)

        accessibility_score = np.clip(scores, 0, 100)
        return accessibility_score
    
    def _calculate_grid_infrastructure_score(self, df):
        """
        Enhanced grid infrastructure scoring combining multiple data sources.
        Returns 0-100 score.
        """
        grid_scores = pd.Series(0, index=df.index)
        
        # Sub-weights for grid components (must sum to 1.0)
        grid_sub_weights = {
            'e3_substations': 0.30,      # E3: Substations IN tract
            'national_grid': 0.35,        # National Grid: Capacity within 5mi
            'ev_readiness': 0.20,         # Existing EV infrastructure readiness
            'feeder_headroom': 0.15       # E3: Feeder capacity
        }
        
        print(f"\n   Enhanced Electric Grid Infrastructure Scoring:")
        
        # ===== E3 Substations (in-tract) =====
        if 'quantity_substations' in df.columns:
            # Direct substations in tract - very valuable
            substation_count = df['quantity_substations'].fillna(0)
            
            # Scoring: 0 = 0 points, 1-2 = good, 3+ = excellent
            # Cap at 5 for normalization
            e3_score = (substation_count.clip(0, 5) / 5.0) * 100
            
            grid_scores += e3_score * grid_sub_weights['e3_substations']
            
            print(f"     E3 Substations (in-tract):")
            print(f"       Tracts with substations: {(substation_count > 0).sum()}")
            print(f"       Avg substations per tract: {substation_count.mean():.2f}")
            print(f"       Max substations: {substation_count.max():.0f}")
            
            # Alternative: use density if available
            if 'substations_per_sq_mi' in df.columns:
                density = df['substations_per_sq_mi'].fillna(0)
                print(f"       Avg density: {density.mean():.3f} per sq mi")
        
        # ===== National Grid (within 5 miles) =====
        if 'ng_grid_capacity_score' in df.columns:
            # Already normalized 0-100 score based on available capacity
            ng_score = df['ng_grid_capacity_score'].fillna(0)
            grid_scores += ng_score * grid_sub_weights['national_grid']
            
            print(f"     National Grid (5mi radius):")
            print(f"       Avg capacity score: {ng_score.mean():.1f}/100")
            
            if 'substations_within_5mi' in df.columns:
                print(f"       Avg substations nearby: {df['substations_within_5mi'].mean():.1f}")
            
            if 'grid_available_capacity_MVA' in df.columns:
                print(f"       Avg available capacity: {df['grid_available_capacity_MVA'].mean():.1f} MVA")
            
            if 'strong_grid_access' in df.columns:
                print(f"       Tracts with strong access (2+): {df['strong_grid_access'].sum()}")
        
        # ===== EV Infrastructure Readiness =====
        if 'ev_infrastructure_readiness' in df.columns:
            readiness_score = df['ev_infrastructure_readiness'].fillna(0)
            grid_scores += readiness_score * grid_sub_weights['ev_readiness']
            
            print(f"     EV Infrastructure Readiness:")
            print(f"       Avg readiness score: {readiness_score.mean():.1f}/100")
            
            if 'electric_pct_high_grade' in df.columns:
                print(f"       Avg % high-grade parcels: {df['electric_pct_high_grade'].mean():.1f}%")
        
        # ===== E3 Feeder Headroom =====
        if 'median_feeder_headroom_mva' in df.columns:
            headroom = df['median_feeder_headroom_mva'].fillna(0)
            
            # Normalize headroom (assume 50+ MVA is excellent)
            if headroom.max() > 0:
                headroom_score = (headroom.clip(0, 50) / 50.0) * 100
            else:
                headroom_score = pd.Series(0, index=df.index)
            
            grid_scores += headroom_score * grid_sub_weights['feeder_headroom']
            
            print(f"     E3 Feeder Headroom:")
            print(f"       Avg headroom: {headroom.mean():.1f} MVA")
            print(f"       Tracts with data: {(headroom > 0).sum()}")
        
        # Final composite grid score
        print(f"     COMPOSITE Grid Score: {grid_scores.mean():.1f}/100")
        
        return grid_scores.clip(0, 100)

    def calculate_equity_feasibility_score(self):
        """Calculate Equity & Environmental score.
    
        Per current dashboard design, this score ONLY uses:
          - EJ Priority Access (benefit)
          - Land Use Suitability / Truck suitability (benefit)
          - Commercial/Industrial land use share (benefit)
          - Protected land penalty (penalty)
    
        Any additional equity/feasibility adjustments (e.g., charging-type-aware EJ scaling,
        sensitive POI penalties, tier bonuses) are intentionally excluded.
        """
        df = self.gdf.copy()
        scores = pd.Series(0, index=df.index)
    
        _equity_defaults = {
            'ej_priority_weight': 0.40,
            'landuse_suit_weight': 0.35,
            'commercial_industrial_weight': 0.15,
            'protected_penalty_weight': 0.10,
        }
        equity_weights = {**_equity_defaults, **(self.config.get('equity_weights') or {})}
    
        # Allow users to disable this entire section
        try:
            eq_total = float(sum([float(v or 0) for v in equity_weights.values()]))
        except Exception:
            eq_total = 1.0
        if eq_total == 0:
            print("   Equity weights set to 0 → equity score disabled")
            return pd.Series(0, index=df.index)
    
        equity_weights = self._normalize_weight_dict(equity_weights)
    
        # Benefit 1: EJ priority access
        if 'ej_priority_score' in df.columns:
            ej_score = self._normalize_score(df['ej_priority_score'])
            scores += ej_score * equity_weights.get('ej_priority_weight', 0)
    
        # Benefit 2: Land use / truck suitability
        if 'truck_suitability_final' in df.columns:
            landuse_suit = self._normalize_score(df['truck_suitability_final'])
            scores += landuse_suit * equity_weights.get('landuse_suit_weight', 0)
    
        # Benefit 3: Commercial + Industrial land use share
        comm = pd.to_numeric(df.get('landuse_pct_commercial', 0), errors='coerce').fillna(0)
        ind  = pd.to_numeric(df.get('landuse_pct_industrial', 0), errors='coerce').fillna(0)
        comm_ind = (comm + ind).clip(0, 100)
        comm_ind_score = self._normalize_score(comm_ind)
        scores += comm_ind_score * equity_weights.get('commercial_industrial_weight', 0)
    
        # Penalty: Protected land share (higher protected = larger penalty)
        protected_col = None
        for col in ['landuse_pct_protected_natural', 'protected_land_pct', 'pct_protected_land']:
            if col in df.columns:
                protected_col = col
                break
        if protected_col is not None:
            protected = pd.to_numeric(df[protected_col], errors='coerce').fillna(0).clip(0, 100)
            protected_score = self._normalize_score(protected)
            scores -= protected_score * equity_weights.get('protected_penalty_weight', 0)
    
        # Clip to 0-100
        equity_score = np.clip(scores, 0, 100)
        return equity_score
    
    def apply_secondary_corridor_filter(self):
        """
        Filter to only secondary corridor tracts.
        
        When enabled, this zeros out all tracts that are NOT on secondary corridors,
        effectively limiting the analysis to secondary corridor sites only.
        
        Returns:
            Boolean mask of tracts on secondary corridors
        """
        df = self.gdf.copy()
        
        if 'is_on_secondary_corridor' in df.columns:
            on_corridor = df['is_on_secondary_corridor'] == 1
            print(f"\n   Secondary corridor filter applied:")
            print(f"     Tracts on secondary corridors: {on_corridor.sum()}")
            print(f"     Tracts filtered out: {(~on_corridor).sum()}")
            return on_corridor
        else:
            print("\n   Warning: Secondary corridor data not available, no filter applied")
            return pd.Series(True, index=df.index)

    def calculate_composite_score(self):
        """
        Calculate weighted composite score for all tracts.
        """
        weights = self.config['weights']

        print("\n" + "=" * 60)
        print("CALCULATING SITE SELECTION SCORES")
        print("=" * 60)

        # Calculate individual component scores
        print("\n1. Calculating demand score...")
        demand = self.calculate_demand_score()
        
        print("\n2. Calculating infrastructure score...")
        infrastructure = self.calculate_infrastructure_score()
        
        print("\n3. Calculating accessibility score...")
        accessibility = self.calculate_accessibility_score()
        
        # NEW: Classify charging types BEFORE equity scoring
        print("\n4. Classifying urban/rural context...")
        urban_rural = self.classify_urban_rural()
        
        print("\n5. Classifying charging facility types...")
        charging_type = self.classify_charging_type()
        
        # NOW calculate equity with charging-type-aware EJ scoring
        print("\n6. Calculating equity & feasibility score (charging-type aware)...")
        equity_feasibility = self.calculate_equity_feasibility_score()

        passes_minimum = self.apply_minimal_constraints()

        # Calculate weighted composite
        composite = (
            demand * weights['demand'] +
            infrastructure * weights['infrastructure'] +
            accessibility * weights['accessibility'] +
            equity_feasibility * weights['equity_feasibility']
        )

        # Zero out tracts that don't pass minimal constraints
        composite = np.where(passes_minimum, composite, 0)
        # Feasible = passes the minimal constraint set
        feasible = passes_minimum

        print(f"   Composite range: {composite[composite > 0].min():.1f} - {composite.max():.1f}")
        print(f"   Composite mean (feasible only): {composite[composite > 0].mean():.1f}")

        # Store scores with ALL metadata including hover info columns
        self.scores = pd.DataFrame({
            'GEOID': self.gdf['GEOID'],
            'NAME': self.gdf.get('NAME', ''),
            'demand_score': demand,
            'infrastructure_score': infrastructure,
            'accessibility_score': accessibility,
            'equity_feasibility_score': equity_feasibility,
            'composite_score': composite,
            'feasible': feasible,
            
            # Temporal metadata
            'temporal_stability': self.gdf.get('truck_temporal_stability_score', 0),
            'temporal_peak_intensity': self.gdf.get('truck_peak_demand_score', 0),
            'demand_uniformity': self.gdf.get('heavy_duty_demand_uniformity', 0),
            'heavy_duty_demand_uniformity': self.gdf.get('heavy_duty_demand_uniformity', 0),
            'heavy_duty_peak_to_avg_ratio': self.gdf.get('heavy_duty_peak_to_avg_ratio', 0),
            
            # Charging type classification
            'charging_type': charging_type,
            'depot_score': self.gdf.get('depot_score', 0),
            'opportunistic_score': self.gdf.get('opportunistic_score', 0),
            'corridor_score': self.gdf.get('corridor_score', 0),
            
            # Urban/rural context
            'urban_rural_context': urban_rural,
            # Explicit rural flag passthrough (needed for UI toggle + rankings table)
            # Prefer rural_flag when present; otherwise derive from common alternatives.
            'rural_flag': (
                self.gdf.get(
                    'rural_flag',
                    self.gdf.get(
                        'is_rural',
                        self.gdf.get(
                            'rural',
                            self.gdf.get('urban_rural_context', '').astype(str).str.strip().str.lower().eq('rural').astype(int)
                            if 'urban_rural_context' in self.gdf.columns else 0
                        )
                    )
                )
            ),
            'urban_context_bonus': self.gdf.get('urban_context_bonus', 0),
            'rural_context_bonus': self.gdf.get('rural_context_bonus', 0),
            'mixed_use_bonus': self.gdf.get('mixed_use_bonus', 0),
            'landuse_diversity_score': self.gdf.get('landuse_diversity_score', 0),
            
            # Domiciled vehicle data (for hover)
            'total_vehicles_domiciled': self.gdf.get('total_vehicles_domiciled', 0),
            'hdt_vehicles_domiciled': self.gdf.get('hdt_vehicles_domiciled', 0),
            'mdt_vehicles_domiciled': self.gdf.get('mdt_vehicles_domiciled', 0),
            'hdt_pct_stops_by_domiciled': self.gdf.get('hdt_pct_stops_by_domiciled', 0),
            
            # Trip data (for hover)
            'Heavy_Duty': self.gdf.get('Heavy_Duty', 0),
            'Medium_Duty': self.gdf.get('Medium_Duty', 0),
            'Light_Duty': self.gdf.get('Light_Duty', 0),
            
            # Stop duration (for hover)
            'avg_stop_duration_minutes': self.gdf.get('avg_stop_duration_minutes', 0),
            'charging_eligible_trip_ends': self.gdf.get('charging_eligible_trip_ends', 0),
            
            # AADT data (for hover)
            'total_daily_heavy_trucks': self.gdf.get('total_daily_heavy_trucks', 0),
            'unique_heavy_trucks_daily': self.gdf.get('unique_heavy_trucks_daily', 0),
            
            # Infrastructure data (for hover)
            'warehouses_within_5mi': self.gdf.get('warehouses_within_5mi', 0),
            'ev_charging_stations_within_5mi': self.gdf.get('ev_charging_stations_within_5mi', 0),
            'park_ride_spaces_within_5mi': self.gdf.get('park_ride_spaces_within_5mi', 0),
            'intermodal_rail_facilities_within_5mi': self.gdf.get('intermodal_rail_facilities_within_5mi', 0),
            
            # Accessibility data (for hover)
            'has_interstate': self.gdf.get('has_interstate', 0),
            'has_nhs_route': self.gdf.get('has_nhs_route', 0),
            'total_road_miles': self.gdf.get('total_road_miles', 0),
            'total_lane_miles': self.gdf.get('total_lane_miles', 0),
            'D3AAO': self.gdf.get('D3AAO', 0),
            
            # Equity data (for hover)
            'ej_priority_score': self.gdf.get('ej_priority_score', 0),
            'pct_ej_block_groups': self.gdf.get('pct_ej_block_groups', 0),
            'truck_suitability_final': self.gdf.get('truck_suitability_final', 0),
            'landuse_pct_commercial': self.gdf.get('landuse_pct_commercial', 0),
            'landuse_pct_industrial': self.gdf.get('landuse_pct_industrial', 0),
            
            # NEW: Co-location opportunities
            'retail_commercial_in_tract': self.gdf.get('retail_commercial_in_tract', 0),
            'retail_in_tract': self.gdf.get('retail_in_tract', 0),
            'gas_stations_in_tract': self.gdf.get('gas_stations_in_tract', 0),
            'hotels_in_tract': self.gdf.get('hotels_in_tract', 0),
            'grocery_stores_in_tract': self.gdf.get('grocery_stores_in_tract', 0),
            'total_poi_in_tract': self.gdf.get('total_poi_in_tract', 0),
            'poi_density_per_sq_mi': self.gdf.get('poi_density_per_sq_mi', 0),
            
            # NEW: Rest stop data
            'rest_stops_within_5mi': self.gdf.get('rest_stops_within_5mi', 0),
            'total_rest_stop_spaces': self.gdf.get('total_rest_stop_spaces', 0),
            'interstate_rest_stops': self.gdf.get('interstate_rest_stops', 0),
            'has_rest_stop_access': self.gdf.get('has_rest_stop_access', 0),
            'rest_stop_priority_score': self.gdf.get('rest_stop_priority_score', 0),
            
            # NEW: Expansion potential
            'estimated_park_ride_area_acres': self.gdf.get('estimated_park_ride_area_acres', 0),
            
            'ev_infrastructure_readiness': self.gdf.get('ev_infrastructure_readiness', 0),
            'electric_grid_suitability': self.gdf.get('electric_grid_suitability', 0),
            'electric_pct_high_grade': self.gdf.get('electric_pct_high_grade', 0),
            'solar_total_capacity_kw': self.gdf.get('solar_total_capacity_kw', 0),
            'solar_potential_kw': self.gdf.get('solar_potential_kw', 0),
            'solar_building_capacity_kw': self.gdf.get('solar_building_capacity_kw', 0),
            'solar_carport_capacity_kw': self.gdf.get('solar_carport_capacity_kw', 0),
            'solar_ground_capacity_kw': self.gdf.get('solar_ground_capacity_kw', 0),
            'electric_avg_suitability': self.gdf.get('electric_avg_suitability', 0),
            
            'is_on_secondary_corridor': self.gdf.get('is_on_secondary_corridor', 0),
            'secondary_corridor_only_score': self.gdf.get('secondary_corridor_only_score', 0),
            'corridor_public_charging_score': self.gdf.get('corridor_public_charging_score', 0),
            'corridor_fleet_hub_score': self.gdf.get('corridor_fleet_hub_score', 0),
        
            # NEW: E3 Substation Data (in-tract)
            'quantity_substations': self.gdf.get('quantity_substations', 0),
            'substations_per_sq_mi': self.gdf.get('substations_per_sq_mi', 0),
            'has_substation_access': self.gdf.get('has_substation_access', 0),
            'median_feeder_headroom_mva': self.gdf.get('median_feeder_headroom_mva', 0),
            'grid_capacity_score': self.gdf.get('grid_capacity_score', 0),  # E3 score
            
            # NEW: National Grid Data (5mi radius)
            'substations_within_5mi': self.gdf.get('substations_within_5mi', 0),
            'grid_renewable_capacity_MW': self.gdf.get('grid_renewable_capacity_MW', 0),
            'grid_load_capacity_MVA': self.gdf.get('grid_load_capacity_MVA', 0),
            'grid_avg_utilization_pct': self.gdf.get('grid_avg_utilization_pct', 0),
            'grid_available_capacity_MVA': self.gdf.get('grid_available_capacity_MVA', 0),
            'ng_grid_capacity_score': self.gdf.get('ng_grid_capacity_score', 0),  # National Grid score
            'has_grid_access': self.gdf.get('has_grid_access', 0),
            'strong_grid_access': self.gdf.get('strong_grid_access', 0),
            'high_capacity_grid': self.gdf.get('high_capacity_grid', 0),
                        
            'geometry': self.gdf.geometry
        })

        print("\n" + "=" * 60)
        print(f"SCORING COMPLETE - {feasible.sum()} feasible sites identified")
        print("=" * 60 + "\n")
        

        return self.scores

    def select_optimal_sites(self, n_sites=4, min_distance_mi=0):
        """
        Select top N sites ensuring geographic diversity.
        Reports charging type distribution in selected sites.
        """
        if self.scores is None:
            raise ValueError("Must run calculate_composite_score() first")

        feasible_scores = self.scores[self.scores['feasible'] == True].copy()
        feasible_scores = feasible_scores.sort_values('composite_score', ascending=False)

        print(f"\nSelecting {n_sites} optimal sites from {len(feasible_scores)} feasible candidates...")
        print(f"Minimum separation: {min_distance_mi} miles")

        selected_sites = []
        selected_geoms = []
        charging_types_selected = []  # NEW: Track types

        for idx, row in feasible_scores.iterrows():
            if len(selected_sites) >= n_sites:
                break

            centroid = row['geometry'].centroid

            if len(selected_geoms) > 0:
                distances = [centroid.distance(g.centroid) * 69 for g in selected_geoms]
                if min(distances) < min_distance_mi:
                    continue

            selected_sites.append(row)
            selected_geoms.append(row['geometry'])
            charging_types_selected.append(row.get('charging_type', 'unclassified'))  # NEW
            
            # Enhanced output showing charging type
            charging_type = row.get('charging_type', 'N/A')
            uniformity = row.get('demand_uniformity', 0)
            print(f"  Site #{len(selected_sites)}: GEOID {row['GEOID']}, Score: {row['composite_score']:.2f}")
            print(f"    Charging type: {charging_type}, Uniformity: {uniformity:.1f}/100")

        if len(selected_sites) < n_sites:
            print(f"\nWarning: Only found {len(selected_sites)} sites meeting criteria (requested {n_sites})")

        # NEW: Report charging type diversity
        if charging_types_selected:
            from collections import Counter
            type_counts = Counter(charging_types_selected)
            print(f"\n  Charging Type Diversity:")
            for ctype, count in type_counts.items():
                print(f"    - {ctype}: {count} site(s)")
            
            # Warn if all sites are the same type
            if len(type_counts) == 1 and list(type_counts.values())[0] > 1:
                print(f"\n  ⚠ Warning: All selected sites are '{list(type_counts.keys())[0]}' type")
                print(f"     Consider adjusting selection criteria for more diversity")

        result_df = pd.DataFrame(selected_sites)
        result_gdf = gpd.GeoDataFrame(result_df, geometry='geometry', crs=self.gdf.crs)

        return result_gdf

    def _normalize_score(self, series):
        """Normalize series to 0-100 scale."""
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        if series.max() > series.min():
            return 100 * (series - series.min()) / (series.max() - series.min())
        return pd.Series(0, index=series.index)
        
        
    def _normalize_score_with_density(self, series, area_col='area_sq_mi', use_density=True):
        """
        Normalize series with optional area-adjustment for spatial fairness.
        
        Args:
            series: The metric to normalize
            area_col: Column name for tract area
            use_density: If True, convert to density (per sq mi) before normalizing
        
        Returns:
            Normalized 0-100 score
        """
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        
        if use_density and area_col in self.gdf.columns:
            # Convert to density to avoid area bias
            area = self.gdf[area_col].replace(0, np.nan)
            density_series = series / area
            density_series = density_series.fillna(0)
            
            # Use percentile-based normalization to handle outliers
            if density_series.max() > density_series.min():
                # Clip extreme outliers at 95th percentile
                p95 = density_series.quantile(0.95)
                clipped = density_series.clip(upper=p95)
                
                if clipped.max() > clipped.min():
                    return 100 * (clipped - clipped.min()) / (clipped.max() - clipped.min())
            
            return pd.Series(0, index=series.index)
        else:
            # Fallback to regular normalization
            return self._normalize_score(series)
        
    
    def classify_charging_type(self):
        """
        Classify each tract into a simple two-category "charging type" proxy based on long-distance trip share.

        Logic:
          - long_distance: %_long_distance_trips > 5
          - other: otherwise

        This classification happens AFTER scoring and serves as a descriptor for filtering and summaries.
        """
        df = self.gdf.copy()

        print("\n" + "=" * 60)
        print("CLASSIFYING CHARGING TYPES (LONG-DISTANCE SHARE)")
        print("=" * 60)

        # Find the long-distance share column (handles a few common naming variants)
        ld_col = None
        for col in ['%_long_distance_trips', 'pct_long_distance_trips', 'percent_long_distance_trips',
                    '% long distance trips', '%_long_distance_trip_ends']:
            if col in df.columns:
                ld_col = col
                break

        if ld_col is None:
            print("  Warning: long-distance share column not found; defaulting all tracts to 'other'")
            charging_type = pd.Series('other', index=df.index)
            ld_share = pd.Series(0.0, index=df.index)
        else:
            ld_share = pd.to_numeric(df[ld_col], errors='coerce').fillna(0)
            # Detect units: some datasets store share as 0-1, others as 0-100
            ld_max = float(ld_share.max()) if len(ld_share) else 0.0
            threshold = 0.05 if ld_max <= 1.0 else 5.0
            charging_type = np.where(ld_share > threshold, 'long_distance', 'other')
            charging_type = pd.Series(charging_type, index=df.index)

        self.gdf['charging_type'] = charging_type
        self.gdf['pct_long_distance_trips'] = ld_share

        print(f"  Long-distance share threshold: > 5% (or >0.05 if stored as 0–1) → 'long_distance'")
        print(f"   - Long-distance: {(charging_type == 'long_distance').sum():4d} tracts")
        print(f"   - Other:         {(charging_type == 'other').sum():4d} tracts")
        print("=" * 60 + "\n")

        return charging_type
        
    
    def classify_urban_rural(self):
        """
        Classify each tract as Urban, Rural, or Mixed based on land use context.
        
        Returns classification that affects scoring weights and infrastructure recommendations.
        """
        df = self.gdf.copy()
        
        print("\n" + "=" * 60)
        print("CLASSIFYING URBAN/RURAL CONTEXT")
        print("=" * 60)
        
        # Initialize classification
        context = pd.Series('unknown', index=df.index)
        
        if 'urban_context_bonus' in df.columns and 'rural_context_bonus' in df.columns:
            urban_bonus = df['urban_context_bonus'].fillna(0)
            rural_bonus = df['rural_context_bonus'].fillna(0)
            mixed_bonus = df.get('mixed_use_bonus', pd.Series(0, index=df.index)).fillna(0)
            
            # Classification logic based on bonuses
            # Urban: High urban bonus, low rural bonus
            is_urban = (urban_bonus > 0) & (rural_bonus == 0)
            
            # Rural: High rural bonus, low urban bonus
            is_rural = (rural_bonus > 0) & (urban_bonus == 0)
            
            # Mixed: Both bonuses present OR mixed_use_bonus present
            is_mixed = ((urban_bonus > 0) & (rural_bonus > 0)) | (mixed_bonus > 0)
            
            # Assign classifications
            context[is_urban] = 'urban'
            context[is_rural] = 'rural'
            context[is_mixed] = 'mixed'
            
            # Use land use diversity as additional signal for mixed areas
            if 'landuse_diversity_score' in df.columns:
                diversity = df['landuse_diversity_score'].fillna(0)
                # High diversity + no clear urban/rural signal = mixed
                high_diversity = diversity > 50
                no_bonus = (urban_bonus == 0) & (rural_bonus == 0)
                context[high_diversity & no_bonus] = 'mixed'
            
            print(f"\n   Classification Summary:")
            print(f"   - Urban:   {(context == 'urban').sum():4d} tracts")
            print(f"   - Rural:   {(context == 'rural').sum():4d} tracts")
            print(f"   - Mixed:   {(context == 'mixed').sum():4d} tracts")
            print(f"   - Unknown: {(context == 'unknown').sum():4d} tracts")
        else:
            print("   Warning: Urban/rural bonus columns not found")
        
        # Store in GeoDataFrame
        self.gdf['urban_rural_context'] = context
        
        print("=" * 60 + "\n")
        
        return context

    def export_results(self, output_path, selected_sites_path=None):
        """Export scored tracts and selected sites to GeoJSON."""
        if self.scores is None:
            raise ValueError("Must run calculate_composite_score() first")

        scored_gdf = gpd.GeoDataFrame(
            self.scores,
            geometry='geometry',
            crs=self.gdf.crs
        )
        scored_gdf.to_file(output_path, driver='GeoJSON')
        print(f"✓ Scored tracts exported to: {output_path}")

        if selected_sites_path:
            selected = self.select_optimal_sites()
            selected.to_file(selected_sites_path, driver='GeoJSON')
            print(f"✓ Selected sites exported to: {selected_sites_path}")
            
    def _calculate_truck_charger_proximity(self):
        """Calculate distance to nearest truck charging station for each tract"""
        from data_loader import get_truck_chargers
        
        print("\n   Calculating proximity to existing truck chargers...")
        
        truck_chargers = get_truck_chargers()
        
        if truck_chargers is None or len(truck_chargers) == 0:
            print("   Warning: No truck charger data available")
            self.gdf['nearest_truck_charger_mi'] = 50.0  # Default to max distance
            return
        
        # Convert to projected CRS for accurate distance (meters)
        gdf_proj = self.gdf.to_crs('EPSG:26986')  # MA State Plane
        chargers_proj = truck_chargers.to_crs('EPSG:26986')
        
        # Calculate distance to nearest charger for each tract
        distances_miles = []
        for tract_geom in gdf_proj.geometry:
            # Distance from tract centroid to all chargers
            dists = chargers_proj.geometry.distance(tract_geom.centroid)
            min_dist_meters = dists.min()
            min_dist_miles = min_dist_meters / 1609.34  # meters to miles
            distances_miles.append(min_dist_miles)
        
        self.gdf['nearest_truck_charger_mi'] = distances_miles
        
        print(f"   ✓ Calculated truck charger proximity:")
        print(f"     Average: {np.mean(distances_miles):.1f} miles")
        print(f"     Min: {np.min(distances_miles):.1f} miles")
        print(f"     Max: {np.max(distances_miles):.1f} miles")

    
    def _is_group_disabled(self, weights: dict, keys: list) -> bool:
        """Return True if the user explicitly set *all* keys in this group to 0.

        We only treat this as 'disabled' when ALL keys are present in the provided
        weights dict and their numeric values sum to 0. This avoids treating missing
        keys (defaults) as a disable signal.
        """
        if not isinstance(weights, dict):
            return False
        if not all(k in weights for k in keys):
            return False
        vals = []
        for k in keys:
            v = weights.get(k, None)
            try:
                v = float(v)
            except Exception:
                return False
            if np.isnan(v):
                return False
            vals.append(v)
        return float(sum(vals)) == 0.0
    
    def _normalize_weight_group(self, weights: dict, keys: list, defaults: list):
        """Normalize a *subset* of weights to sum to 1.0.

        This is used for demand subfactor groups (vehicle class, trip type, etc.).
        The user may provide either fractional weights (sum ~1) or integer points
        (sum ~100). Either way, we normalize within the group only.

        Returns:
            tuple of normalized weights in the same order as `keys`.
        """
        vals = []
        for k, d in zip(keys, defaults):
            v = weights.get(k, d) if isinstance(weights, dict) else d
            try:
                v = float(v)
            except Exception:
                v = float(d)
            if np.isnan(v):
                v = float(d)
            vals.append(v)

        s = float(sum(vals))
        if s == 0:
            # fall back to defaults (already fractional)
            vals = [float(d) for d in defaults]
            s = float(sum(vals))
            if s == 0:
                # last resort: equal weights
                n = max(1, len(vals))
                return tuple([1.0 / n] * n)

        return tuple([v / s for v in vals])

    def _normalize_weight_dict(self, weights: dict) -> dict:
        """Normalize a weight dictionary to sum to 1.0.

        Accepts either fractional weights (sum ~1.0) or integer points (e.g., sum ~100).
        """
        if not weights:
            return {}
        vals = [v for v in weights.values() if v is not None]
        try:
            s = float(sum(vals))
        except Exception:
            return weights
        if s == 0:
            return weights
        # already fractional
        if s <= 1.5:
            return weights
        return {k: (float(v) / s) if v is not None else 0.0 for k, v in weights.items()}



