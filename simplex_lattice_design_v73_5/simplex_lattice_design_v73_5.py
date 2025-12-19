def simplex_lattice_design_v73_5():
    r"""
    # Overview
    The `simplex_lattice_design_v73_5` function is a comprehensive formulation tool designed to generate Simplex-Lattice mixture designs.
    It translates active ingredient targets into practical product masses and volumes, handling raw material purity, density, and
    complex mass balance logic where impurities of ingredients are considered part of the solvent system.

    # Core Logic and Rules
    1.  **Lattice Generation:**
        -   Constructs a standard simplex lattice coordinate matrix based on `Degree (m)` (step size = $1/m$).
    2.  **Product Calculation:**
        -   **Target Active (i)** is derived from the lattice fraction scaled by `Max Active %`.
        -   **Product Mass (i)** is calculated to achieve the target active active mass given the ingredient's purity.
        -   **Product Volume (i)** = $\frac{Product\_Mass_i}{Density_i}$.
        -   **Mass Closure:** The sum of all product masses must equal `Total Formula Mass` ($\pm$ 1%).
    3.  **Active & Impurity Logic:**
        -   **Intrinsic Active Mass (i)** = Product Mass (i) $\times$ Purity (i).
        -   **Impurity Mass (i)** = Product Mass (i) $\times$ (1 - Purity (i)).
    4.  **Solvent Logic ('is_solvent'):**
        -   **False (Standard Ingredient):**
            -   Active Content = Intrinsic Active Mass (i).
            -   Active % = (Intrinsic Active Mass (i) / Total Formula Mass) * 100.
        -   **True (Solvent Ingredient):**
            -   Calculated as the filler to reach `Total Formula Mass`.
            -   **Total Solvent Active Mass** = Intrinsic Active Mass (Solvent) + $\sum$(Impurity Mass of ALL ingredients).
            -   *Concept:* Impurities of all ingredients are treated as the same chemical species as the solvent's active.
            -   Active % = (Total Solvent Active Mass / Total Formula Mass) * 100.
            -   **Column Renaming:** If marked as solvent:
                -   Active Wt% column becomes 'Component i (Component Active + Solvent as active, wt) [%]'.
                -   Active Mass column becomes 'Component i (Active Mass + Solvent as active) [g]'.

    # Visuals
    -   **Plot Selection:** Users must select exactly 3 ingredients via checkboxes to generate a Ternary Diagram (or 2 for Binary).
    -   **N=2:** Interactive Binary Scatter plot.
    -   **N=3:** Interactive Ternary Diagram (1000x625px). Points are blue with black borders.
        -   *Filter:* Points where non-selected ingredients > 0 are hidden in the ternary plot to ensure a true slice.
        -   *Title Logic:*
            -   If **No Solvent** is selected: Title indicates "Normalized Product Weight %" (as points are relative).
            -   If **Solvent** is selected: Title indicates "Product Weight %".
    -   **Formatting:** Axes labels always show exactly 1 decimal place (e.g., '20.0').

    # Parameters (GUI Inputs)
    -   **Global:** Degree, Total Mass, Replicates, Randomize.
    -   **Ingredients:** Select (for plot), Name, Purity (%), Max Active (%), Density (g/mL), Is Solvent.

    # Returns
    -   Interactive Widget Interface.
    -   Styled Data Table (4 decimal precision).
    -   Plotly Figures.
    -   **Excel Export (.xlsx):**
        -   **Sheet 1 (Datapoints):** The full design table.
        -   **Sheet 2 (Parameters):** A log of all input settings used to generate the design.

    # Change Log
    -   **v73.5 (Dec/18/2025):**
        -   **Visuals:** Adjusted top margins and y-position of the Ternary Plot title to accommodate the two-line dynamic title without overlapping or clipping.
    -   **v73.4 (Dec/18/2025):**
        -   **Visuals:** Updated the Ternary Plot title to dynamically show the unit type.
    -   **v73.3 (Dec/18/2025):**
        -   **Output:** Added formulation count display.
    -   **v73.2 (Dec/18/2025):**
        -   **Logic/Formatting:** Renamed 'Active Mass' column for solvent ingredients.
    -   **v73.1 (Dec/18/2025):**
        -   **UI:** Added explanatory note for "No Solvent" scenario.
    -   **v73.0 (Dec/18/2025):**
        -   **UI Layout:** Widened inputs.
    -   **v72.0 (Dec/18/2025):**
        -   **UI Defaults:** Default component names. Table True by default.
        -   **Logic:** Dynamic column renaming.
    -   **v71.0 (Dec/18/2025):**
        -   **Logic:** Impurity handling. Excel export updates.

    # Test Example
    ```python
    # To run the interface simply call:
    simplex_lattice_design_v73_5()
    ```

    # Credits
    -   **Author:** Manazael Zuliani Jora
    -   **Date:** Dec/18/2025
    """

    # ==============================================================================
    # 0. IMPORTS & ENVIRONMENT
    # ==============================================================================
    import pandas as pd
    import numpy as np
    import itertools
    import plotly.express as px
    import plotly.colors as pcolors
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import ipywidgets as widgets
    from datetime import datetime
    from IPython.display import display, Markdown, clear_output, HTML
    from pandas.io.formats.style import Styler
    import math
    import io

    # Try enabling Custom Widgets for Google Colab automatically
    try:
        from google.colab import output
        output.enable_custom_widget_manager()
    except ImportError:
        pass

    # Try importing openpyxl
    try:
        import openpyxl
    except ImportError:
        pass

    # ==============================================================================
    # 1. CALCULATION LOGIC
    # ==============================================================================
    def calculate_design(component_data, degree_m, total_formula_mass, replicate, randomize):
        solvent_component_name = None
        component_names = list(component_data.keys())

        # Validation: Solvent Count
        solvent_count = sum(1 for data in component_data.values() if data.get('is_solvent', False))
        if solvent_count > 1:
            raise ValueError("Error: Multiple ingredients marked as 'Is Solvent'. Only 1 is allowed.")
        
        # Identify Solvent
        for name, data in component_data.items():
            if data.get('is_solvent', False):
                solvent_component_name = name

        # Map Data
        product_purity_map = {} # 0 to 1
        max_active_map = {}     # 0 to 1
        density_map = {}
        
        # Mapping for column headers
        active_wt_col_map = {}
        active_mass_col_map = {}

        for name, values_dict in component_data.items():
            p_act = values_dict.get('product_active_wt_perc')
            m_act = values_dict.get('maximum_active_wt_perc')
            dens = values_dict.get('density', 1.0)
            is_solv = values_dict.get('is_solvent', False)
            
            # Validation: Max <= Purity
            if m_act > p_act:
                raise ValueError(f"CRITICAL: {name} - Max Active ({m_act}%) > Purity ({p_act}%). Impossible to achieve.")
            
            if p_act < 0 or p_act > 100 or m_act < 0 or m_act > 100:
                 raise ValueError(f"CRITICAL: Percentages must be 0-100. Check {name}.")

            if dens <= 0:
                raise ValueError(f"Error: {name} density must be > 0.")
            
            product_purity_map[name] = p_act / 100.0
            max_active_map[name] = m_act / 100.0
            density_map[name] = dens
            
            # Set Column Names dynamically
            if is_solv:
                active_wt_col_map[name] = f'{name} (Component Active + Solvent as active, wt) [%]'
                active_mass_col_map[name] = f'{name} (Active Mass + Solvent as active) [g]'
            else:
                active_wt_col_map[name] = f'{name} (Active wt) [%]'
                active_mass_col_map[name] = f'{name} (Active Mass) [g]'

        valid_rows, removed_rows = [], []
        
        # Generate Lattice Points (z vector)
        for p_tuple in itertools.product(range(degree_m + 1), repeat=len(component_names)):
            if sum(p_tuple) == degree_m:
                z = [x / degree_m for x in p_tuple]
                
                row_data = {}
                temp_product_masses = {}

                # 1. Calculate Product Masses for Non-Solvents based on Max Active Constraints
                calc_names = [n for n in component_names if n != solvent_component_name]
                sum_partial_mass = 0.0

                for name in calc_names:
                    idx = component_names.index(name)
                    # Target Active Mass = Lattice_Fraction * Max_Limit * Total_Mass
                    target_active_mass = (z[idx] * max_active_map[name]) * total_formula_mass
                    purity = product_purity_map[name]
                    
                    # Product Mass = Target Active / Purity
                    prod_mass = target_active_mass / purity if purity > 0 else 0
                    temp_product_masses[name] = prod_mass
                    sum_partial_mass += prod_mass

                # 2. Calculate Solvent Mass (Filler)
                if solvent_component_name:
                    req_solvent_mass = total_formula_mass - sum_partial_mass
                    temp_product_masses[solvent_component_name] = req_solvent_mass
                
                # Check Mass Closure
                final_sum_mass = sum(temp_product_masses.values())
                is_valid, reason = True, ""

                # Tolerance 1%
                if final_sum_mass > (total_formula_mass * 1.01):
                    reason, is_valid = "Sum(Product) > Total Mass", False
                elif final_sum_mass < (total_formula_mass * 0.99) and solvent_component_name:
                     if temp_product_masses[solvent_component_name] < 0:
                         reason, is_valid = "Negative Solvent Required", False

                # 3. Calculate Properties (Volumes, Active Masses, Impurities)
                sum_active_wt, sum_prod_wt = 0.0, 0.0
                
                # First pass: Calculate Intrinsic Active and Impurity for ALL ingredients
                intrinsic_actives = {}
                impurities = {}

                for name in component_names:
                    p_mass = temp_product_masses.get(name, 0.0)
                    purity = product_purity_map[name]
                    intrinsic_actives[name] = p_mass * purity
                    impurities[name] = p_mass * (1.0 - purity)

                total_impurity_mass = sum(impurities.values())

                # Second pass: Assign values to row
                for name in component_names:
                    p_mass = temp_product_masses.get(name, 0.0)
                    p_vol = p_mass / density_map[name]
                    
                    p_wt = (p_mass / total_formula_mass) * 100.0 if total_formula_mass > 0 else 0

                    row_data[f'{name} (Product mass) [g]'] = p_mass
                    row_data[f'{name} (Product volume) [mL]'] = p_vol
                    row_data[f'{name} (Product wt) [%]'] = p_wt
                    row_data[f'{name} (Impurity Mass) [g]'] = impurities[name]

                    # Final Active Calculation Logic
                    if name == solvent_component_name:
                        # Solvent Active = Intrinsic Solvent Active + Sum of ALL Impurities
                        final_active_mass = intrinsic_actives[name] + total_impurity_mass
                    else:
                        # Non-Solvent Active = Intrinsic Only
                        final_active_mass = intrinsic_actives[name]
                    
                    # Store Active Mass using dynamic key
                    row_data[active_mass_col_map[name]] = final_active_mass

                    a_wt = (final_active_mass / total_formula_mass) * 100.0 if total_formula_mass > 0 else 0
                    
                    # Store Active Wt using dynamic key
                    row_data[active_wt_col_map[name]] = a_wt

                    sum_active_wt += a_wt
                    sum_prod_wt += p_wt

                row_data['Sum (Product mass) [g]'] = final_sum_mass
                row_data['Sum (Product weight) [%]'] = sum_prod_wt
                row_data['Sum (Active weight) [%]'] = sum_active_wt
                row_data['Reason Removed'] = reason

                # Check Active Limit > 100%
                if sum_active_wt > 100.01:
                    is_valid, reason = False, "Sum(Active) > 100%"
                    row_data['Reason Removed'] = reason

                if is_valid: valid_rows.append(row_data)
                else: removed_rows.append(row_data)

        # Define Column Order
        col_prod_mass = [f'{n} (Product mass) [g]' for n in component_names]
        col_prod_vol = [f'{n} (Product volume) [mL]' for n in component_names]
        col_imp_mass = [f'{n} (Impurity Mass) [g]' for n in component_names]
        col_prod_wt = [f'{n} (Product wt) [%]' for n in component_names]
        
        # Dynamic columns
        col_active_mass = [active_mass_col_map[n] for n in component_names]
        col_active_wt = [active_wt_col_map[n] for n in component_names]

        base_cols = ['Formula Number'] + col_prod_mass + col_prod_vol + col_active_mass + col_imp_mass + col_prod_wt + col_active_wt
        summ_cols = ['Sum (Product mass) [g]', 'Sum (Product weight) [%]', 'Sum (Active weight) [%]']
        final_cols = base_cols + summ_cols

        # Create DataFrame
        df_valid = pd.DataFrame(valid_rows)
        if not df_valid.empty:
            if replicate > 1:
                df_valid = pd.concat([df_valid] * int(replicate), ignore_index=True)
            if randomize:
                df_valid = df_valid.sample(frac=1).reset_index(drop=True)
            
            df_valid.insert(0, 'Formula Number', range(1, len(df_valid) + 1))
            df_valid = df_valid.reindex(columns=final_cols)

        df_removed = pd.DataFrame(removed_rows)
        if not df_removed.empty:
            cols_rem = ['Reason Removed'] + [c for c in final_cols if c != 'Formula Number']
            df_removed = df_removed.reindex(columns=cols_rem)
        
        # Color Palette Generation
        base_palette = px.colors.qualitative.Plotly + px.colors.qualitative.Bold + px.colors.qualitative.Dark24
        while len(base_palette) < len(component_names): base_palette += base_palette
        colors_hex = [base_palette[i] for i in range(len(component_names))]

        return df_valid, df_removed, colors_hex, component_names, final_cols, active_wt_col_map

    # ==============================================================================
    # 2. UI & INTERACTION
    # ==============================================================================

    # Custom CSS for Gray/Black Theme
    style_css = """
    <style>
    .interface-container {
        background-color: #F0F0F0;
        border: 2px solid black;
        padding: 20px;
        border-radius: 5px;
    }
    .widget-label { font-weight: bold; font-size: 14px; color: black !important; }
    .header-text { font-size: 20px; font-weight: bold; border-bottom: 2px solid black; padding-bottom: 5px; margin-bottom: 15px; color: black; }
    .sub-header { font-size: 16px; font-weight: bold; margin-top: 10px; color: black; }
    
    /* Box container for ingredient rows */
    .ing-box {
        border: 1px solid #999;
        background-color: #E8E8E8;
        padding: 5px;
        margin-bottom: 5px;
        border-radius: 4px;
        overflow-x: auto; /* Handle overflow if rows are very wide */
    }

    /* Input Styling */
    .widget-text input, .widget-readout input, .widget-hslider input {
        background-color: #808080 !important;
        color: white !important;
        border: 1px solid black;
        font-weight: bold;
        font-size: 13px;
        padding: 4px;
    }
    
    /* Arrows (Spinners) inside inputs */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: inner-spin-button !important;
        opacity: 1 !important;
        background: #dddddd !important;
        filter: invert(0); 
        height: 100%;
        display: block;
        cursor: pointer;
        margin-left: 2px;
    }
    
    .widget-checkbox > label { color: black !important; font-weight: bold; }
    </style>
    """
    display(HTML(style_css))

    # --- Widgets ---
    # Global Settings
    w_degree = widgets.BoundedIntText(value=3, min=1, max=15, description='Degree (m):', style={'description_width': 'initial'}, layout=widgets.Layout(width='200px'))
    w_mass = widgets.FloatText(value=100.0, description='Total Mass (g):', style={'description_width': 'initial'}, layout=widgets.Layout(width='220px'))
    w_reps = widgets.BoundedIntText(value=1, min=1, max=10, description='Replicates:', style={'description_width': 'initial'}, layout=widgets.Layout(width='200px'))
    
    w_rand = widgets.Checkbox(value=False, description='Randomize')
    w_csv = widgets.Checkbox(value=False, description='Export Excel (.xlsx)')
    w_plot = widgets.Checkbox(value=True, description='Show Plot')
    w_table = widgets.Checkbox(value=True, description='Show Table')

    rows_container = widgets.VBox([])
    component_rows = []

    def on_solvent_change(change):
        if change['new']:
            for row in component_rows:
                if row['w_solvent'] != change['owner']: row['w_solvent'].value = False

    def add_ingredient_row(b=None, initial_data=None):
        idx = len(component_rows) + 1
        default_sel = False
        if initial_data: default_sel = initial_data.get('sel', False)
        
        data = initial_data if initial_data else {'name': f'Component {idx}', 'purity': 100.0, 'max': 100.0, 'dens': 1.0, 'solvent': False}

        w_select = widgets.Checkbox(value=default_sel, indent=False, layout=widgets.Layout(width='30px'))
        
        # Name: 80 chars approx 600px width
        w_name = widgets.Text(value=data['name'], placeholder='Name', description='Name:', 
                              layout=widgets.Layout(width='600px'), style={'description_width': '50px'})

        # Numeric Fields: 16 chars approx ~230-250px
        w_purity = widgets.BoundedFloatText(value=data['purity'], min=0.0, max=100.0, step=1.0, description='Purity (%):', 
                                            layout=widgets.Layout(width='230px'), style={'description_width': '80px'})

        w_max = widgets.BoundedFloatText(value=data['max'], min=0.0, max=100.0, step=1.0, description='Max Active (%):', 
                                         layout=widgets.Layout(width='250px'), style={'description_width': '110px'})

        w_dens = widgets.BoundedFloatText(value=data.get('dens', 1.0), min=0.01, max=20.0, step=0.01, description='Density (g/mL):', 
                                          layout=widgets.Layout(width='250px'), style={'description_width': '110px'})

        w_solvent = widgets.Checkbox(value=data['solvent'], description='Is Solvent', indent=False, layout=widgets.Layout(width='100px'))
        w_solvent.observe(on_solvent_change, names='value')

        btn_del = widgets.Button(icon='trash', button_style='danger', layout=widgets.Layout(width='40px', height='30px'))

        row_hbox = widgets.HBox([w_select, w_name, w_purity, w_max, w_dens, w_solvent, btn_del], 
                                layout=widgets.Layout(align_items='center', margin='4px 0'))
        row_hbox.add_class('ing-box')

        def delete_row(btn):
            if row_hbox in rows_container.children:
                new_list = list(rows_container.children)
                new_list.remove(row_hbox)
                rows_container.children = tuple(new_list)
            for i, r in enumerate(component_rows):
                if r['hbox'] is row_hbox: component_rows.pop(i); break

        btn_del.on_click(delete_row)
        component_rows.append({
            'hbox': row_hbox, 'w_select': w_select, 'w_name': w_name, 
            'w_purity': w_purity, 'w_max': w_max, 'w_dens': w_dens, 'w_solvent': w_solvent
        })
        rows_container.children += (row_hbox,)

    btn_add = widgets.Button(description='Add Ingredient', icon='plus', button_style='info', layout=widgets.Layout(width='150px', margin='0 0 10px 0'))
    btn_add.on_click(add_ingredient_row)

    btn_run = widgets.Button(description='GENERATE DESIGN', button_style='success', icon='cogs', layout=widgets.Layout(width='100%', height='50px', margin='20px 0'))
    out_display = widgets.Output()

    # --- Run Handler ---
    def on_run(b):
        out_display.clear_output()
        comp_data = {}
        
        if len(component_rows) < 2:
            with out_display: display(HTML("<b style='color:red'>⚠️ Needs at least 2 ingredients.</b>"))
            return

        selected_for_plot = []
        has_solvent = False

        for row in component_rows:
            c_name = row['w_name'].value.strip() or "Unnamed"
            is_solv = row['w_solvent'].value
            if is_solv: has_solvent = True
            
            comp_data[c_name] = {
                'product_active_wt_perc': row['w_purity'].value,
                'maximum_active_wt_perc': row['w_max'].value,
                'density': row['w_dens'].value,
                'is_solvent': is_solv
            }
            if row['w_select'].value:
                selected_for_plot.append(c_name)

        results_widgets = []
        results_widgets.append(widgets.HTML("<b style='color:black; font-size:18px;'>--- Running Simplex Lattice Design v73.5 ---</b>"))
        
        try:
            df_valid, df_removed, colors_hex, component_names, final_cols, active_col_map = calculate_design(
                comp_data, w_degree.value, w_mass.value, w_reps.value, w_rand.value
            )
            
            # Show Count of Formulations
            n_forms = len(df_valid)
            results_widgets.append(widgets.HTML(f"<span style='color:black; font-size:14px; font-weight:bold;'>Generated {n_forms} formulations.</span>"))
            results_widgets.append(widgets.HTML("<br>"))

            # --- 1. Validation & Removed Formulas ---
            if not df_removed.empty:
                results_widgets.append(widgets.HTML(f"<div class='sub-header' style='color:red'>⚠️ WARNING: {len(df_removed)} Formulas Removed (Constraint Violated)</div>"))
                styler_rem = df_removed.style.format(precision=4)
                styler_rem.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#d9534f'), ('color', 'white'), ('font-weight', 'bold'), ('text-align', 'center'), ('border', '1px solid black')]},
                    {'selector': 'td', 'props': [('text-align', 'center'), ('border', '1px solid black')]}
                ])
                styler_rem.set_properties(subset=['Reason Removed'], **{'color': 'red', 'font-weight': 'bold'})
                results_widgets.append(widgets.HTML(styler_rem.to_html()))
                results_widgets.append(widgets.HTML("<hr>"))

            # --- 2. Visualization ---
            if w_plot.value and not df_valid.empty:
                results_widgets.append(widgets.HTML("<div class='sub-header'>Visualization</div>"))
                
                n_sel = len(selected_for_plot)
                if n_sel < 2 or n_sel > 3:
                    results_widgets.append(widgets.HTML(f"<b style='color:orange'>⚠️ Plot skipped: Select exactly 2 or 3 ingredients via checkboxes. (Selected: {n_sel})</b>"))
                else:
                    df_plot = df_valid.copy()
                    df_hover = df_valid.copy()
                    for c in df_valid.columns:
                        if pd.api.types.is_float_dtype(df_valid[c]): df_hover[c] = df_hover[c].apply(lambda x: f"{x:.4f}")
                    
                    custom_data = df_hover[final_cols].values

                    # Hover Template
                    def create_hover():
                        ht = "<b>Formula %{customdata[0]}</b><br>──────────────<br>"
                        # Show first 3 components in hover to keep it clean, or all if small number
                        limit_hover = min(len(component_names), 3)
                        for i in range(limit_hover):
                            name = component_names[i]
                            color = colors_hex[i]
                            ht += f"<b style='color:{color}'>{name}</b><br>"
                            ht += f"Mass: %{{customdata[{final_cols.index(f'{name} (Product mass) [g]')}]}} g<br>"
                            ht += f"Vol: %{{customdata[{final_cols.index(f'{name} (Product volume) [mL]')}]}} mL<br>"
                            ht += f"Wt: %{{customdata[{final_cols.index(f'{name} (Product wt) [%]')}]}} %<br><br>"
                        
                        ht += "<b>Totals</b><br>"
                        ht += f"Mass: %{{customdata[{final_cols.index('Sum (Product mass) [g]')}]}} g<br>"
                        ht += "<extra></extra>"
                        return ht

                    fig = None
                    
                    # Determine Plot Title Suffix based on Solvent Presence
                    plot_title_suffix = "Product Weight %" if has_solvent else "Normalized Product Weight %"

                    # --- Ternary Plot ---
                    if n_sel == 3:
                        name_a, name_b, name_c = selected_for_plot
                        
                        # Filter: Only show points where other components are effectively 0
                        others = set(component_names) - set(selected_for_plot)
                        mask = pd.Series([True]*len(df_plot))
                        for o in others: 
                            mask &= (df_plot[f'{o} (Product mass) [g]'] <= 0.01)
                        
                        plot_data = df_plot[mask]

                        if not plot_data.empty:
                            fig = px.scatter_ternary(plot_data, 
                                                     a=f'{name_a} (Product wt) [%]', 
                                                     b=f'{name_c} (Product wt) [%]', 
                                                     c=f'{name_b} (Product wt) [%]') 

                            # Re-map indices for colors
                            idx_a = component_names.index(name_a)
                            idx_b = component_names.index(name_b)
                            idx_c = component_names.index(name_c)
                            
                            def get_axis(color):
                                return dict(title='', tickfont=dict(size=18, family="Arial Black", color='black'),
                                            ticklen=15, tickwidth=3, linewidth=5, linecolor=color,
                                            gridcolor=color, griddash='dash', gridwidth=1, ticks='outside', layer='below traces',
                                            dtick=20, tickformat='.1f')

                            fig.update_layout(width=1000, height=625,
                                              title=dict(text=f'<b>Simplex Lattice - {plot_title_suffix}<br>({name_a}; {name_b}; {name_c})</b>', x=0.5, y=0.96, font=dict(size=24, color='black')),
                                              margin=dict(l=100, r=100, t=190, b=150),
                                              ternary=dict(sum=100,
                                                           aaxis=get_axis(colors_hex[idx_a]),
                                                           baxis={**get_axis(colors_hex[idx_c]), 'tickangle': 60},
                                                           caxis={**get_axis(colors_hex[idx_b]), 'tickangle': -60},
                                                           bgcolor='#f9f9f9'))

                            # Annotations for Axes Titles
                            fig.add_annotation(x=0.5, y=1.3, text=f"<b>{name_a}</b>", showarrow=False, font=dict(color=colors_hex[idx_a], size=22))
                            fig.add_annotation(x=0.1, y=-0.35, text=f"<b>{name_c}</b>", showarrow=False, font=dict(color=colors_hex[idx_c], size=22))
                            fig.add_annotation(x=0.9, y=-0.35, text=f"<b>{name_b}</b>", showarrow=False, font=dict(color=colors_hex[idx_b], size=22))
                            
                            sub_custom = df_hover.loc[plot_data.index, final_cols].values
                            fig.update_traces(customdata=sub_custom, hovertemplate=create_hover(),
                                              marker=dict(size=18, color='#1f77b4', line=dict(width=2, color='black')),
                                              cliponaxis=False)
                        else:
                            results_widgets.append(widgets.HTML("<i style='color:red'>No valid points found for this strict ternary combination (others must be 0).</i>"))

                    # --- Binary Plot ---
                    elif n_sel == 2:
                        name_a, name_b = selected_for_plot
                        others = set(component_names) - set(selected_for_plot)
                        mask = pd.Series([True]*len(df_plot))
                        for o in others: mask &= (df_plot[f'{o} (Product mass) [g]'] <= 0.01)
                        plot_data = df_plot[mask]

                        if not plot_data.empty:
                            fig = px.scatter(plot_data, x=f'{name_a} (Product wt) [%]', y=f'{name_b} (Product wt) [%]')
                            fig.update_layout(title=dict(text=f'<b>{name_a} vs {name_b} ({plot_title_suffix})</b>', font=dict(size=24, color='black')),
                                              xaxis=dict(title=f"<b>{name_a} [%]</b>", tickfont=dict(size=18), gridcolor='#ddd', dtick=20, tickformat='.1f'),
                                              yaxis=dict(title=f"<b>{name_b} [%]</b>", tickfont=dict(size=18), gridcolor='#ddd', dtick=20, tickformat='.1f'))
                            sub_custom = df_hover.loc[plot_data.index, final_cols].values
                            fig.update_traces(customdata=sub_custom, hovertemplate=create_hover(),
                                              marker=dict(size=18, color='#1f77b4', line=dict(width=2, color='black')),
                                              cliponaxis=False)
                        else:
                            results_widgets.append(widgets.HTML("<i style='color:red'>No valid points found for this combination.</i>"))

                    if fig: results_widgets.append(go.FigureWidget(fig))
                    results_widgets.append(widgets.HTML("<br>"))

            # --- 3. Design Table ---
            if w_table.value and not df_valid.empty:
                results_widgets.append(widgets.HTML("<div class='sub-header'>Design Table (Valid Formulas)</div>"))
                styler = df_valid.style.format(precision=4)
                
                # Header and Row Styles
                styler.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#2c3e50'), ('color', 'white'), ('font-weight', 'bold'), ('text-align', 'center'), ('border', '1px solid black')]},
                    {'selector': 'td', 'props': [('text-align', 'center'), ('border', '1px solid black')]},
                    {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#E0E0E0'), ('color', 'black')]},
                    {'selector': 'tr:nth-child(odd)', 'props': [('background-color', '#D3D3D3'), ('color', 'black')]}
                ])
                # Color code columns per ingredient
                for i, name in enumerate(component_names):
                    styler.set_properties(subset=[c for c in df_valid.columns if c.startswith(name)], **{'color': colors_hex[i], 'font-weight': 'bold'})
                
                results_widgets.append(widgets.HTML(styler.to_html()))

            # --- 4. No Output Warning ---
            if not w_plot.value and not w_table.value:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                results_widgets.append(widgets.HTML(f"<i>Points generated at {now_str}, but both Table and Plot are False.</i>"))

            # --- 5. EXPORT Logic ---
            if w_csv.value and not df_valid.empty:
                fname = f'simplex_lattice_design_v73_5_{datetime.now().strftime("%H%M%S")}.xlsx'
                
                import importlib.util
                if importlib.util.find_spec("openpyxl") is None:
                      with out_display: display(HTML("<b style='color:red'>❌ Error: 'openpyxl' is missing. Cannot export Excel.</b>"))
                else:
                    # 5a. Create Parameters Sheet
                    params_data = [
                        ['Global Settings', ''],
                        ['Degree (m)', w_degree.value],
                        ['Total Mass (g)', w_mass.value],
                        ['Replicates', w_reps.value],
                        ['Randomize', w_rand.value],
                        ['Timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                        ['', ''],
                        ['Ingredients Config', ''],
                        ['Name', 'Purity (%) | Max Active (%) | Density | Is Solvent']
                    ]
                    for name, data in comp_data.items():
                        info_str = f"{data['product_active_wt_perc']} | {data['maximum_active_wt_perc']} | {data['density']} | {data['is_solvent']}"
                        params_data.append([name, info_str])
                    
                    df_params = pd.DataFrame(params_data, columns=['Parameter', 'Value'])
                    
                    # 5b. Write Excel
                    with pd.ExcelWriter(fname) as writer:
                        df_valid.to_excel(writer, sheet_name='Datapoints', index=False)
                        df_params.to_excel(writer, sheet_name='Parameters', index=False)
                    
                    results_widgets.append(widgets.HTML(f"<br><b style='color:green'>✅ Excel Exported: {fname}</b>"))

            with out_display:
                display(widgets.VBox(results_widgets))

        except Exception as e:
            with out_display:
                display(HTML(f"<b style='color:red'>⛔ Error: {str(e)}</b>"))
                import traceback
                traceback.print_exc()

    btn_run.on_click(on_run)

    # UI Layout Construction
    ui_content = [
        widgets.HTML("<div class='header-text'>🧪 Simplex Lattice Design v73.5</div>"),
        widgets.HTML("<div class='sub-header'>1. Global Settings</div>"),
        widgets.HBox([w_degree, w_mass, w_reps]),
        widgets.HBox([w_plot, w_table, w_csv, w_rand]),
        widgets.HTML("<hr>"),
        widgets.HTML("<div class='sub-header'>2. Ingredients (Select 3 for Ternary, 2 for Binary)</div>"),
        widgets.HTML("<i style='color:black'>Config: Name | Purity (%) | Max Active (%) | Density | Is Solvent</i>"),
        widgets.HTML("<span style='color:black; font-size:12px;'>Note: If no ingredient is marked as a solvent, the total mass becomes a reference only (so that no solvent needs to be added), and not the total sum of the products to be weighed.</span>"),
        btn_add, 
        rows_container, 
        widgets.HTML("<hr>"), 
        btn_run, 
        out_display
    ]
    ui = widgets.VBox(ui_content)
    ui.add_class('interface-container')

    # Defaults
    defaults = [
        {'name': 'Component 1', 'purity': 100.0, 'max': 100.0, 'dens': 1.0, 'solvent': False, 'sel': True},
        {'name': 'Component 2', 'purity': 100.0, 'max': 100.0, 'dens': 1.0, 'solvent': False, 'sel': True},
        {'name': 'Component 3', 'purity': 100.0, 'max': 100.0, 'dens': 1.0, 'solvent': False, 'sel': True}
    ]
    for d in defaults: add_ingredient_row(initial_data=d)

    display(ui)

# Run the Interface
simplex_lattice_design_v73_5()
