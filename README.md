# Overview
    The `simplex_lattice_design_v70_7` function is a comprehensive formulation tool designed to generate Simplex-Lattice mixture designs. 
    It enables formulation scientists to translate active ingredient targets into practical product masses and volumes, 
    handling raw material purity, density, and complex solvent balancing logic.

    # Core Logic and Rules
    1.  **Lattice Generation:**
        -   Constructs a standard simplex lattice coordinate matrix ($z$) based on `Degree (m)` (step size = $1/m$).
    2.  **Concentration Scaling:**
        -   **Target Active (i)** = $Base\_Conc_i \times Max\_Active\_Limit_i$.
    3.  **Product Calculation:**
        -   **Product Mass (i)** = $\frac{Target\_Active_i}{Purity_i} \times Total\_Formula\_Mass$.
    4.  **Solvent Logic ('is_solvent'):**
        -   **True (Solvent):** Calculated as filler to reach `Total Mass`.
        -   **False (Active/No Solvent):**
            -   Initial masses calculated based on lattice proportions.
            -   **Normalization:** If no solvent is selected, all product masses are proportionally scaled so their sum equals `Total Mass`.
    5.  **Validation:**
        -   **Mass Closure:** Sum of products must equal Total Mass ($\pm$ 1%).
        -   **Active Limit:** Sum of active percentages must not exceed 100%.
        -   **Purity Check:** Max Active Limit must be $\le$ Product Purity.

    # Visuals
    -   **Plot Selection:** Users must select exactly 3 ingredients via checkboxes to generate a Ternary Diagram (or 2 for a Binary Plot).
    -   **N=2:** Interactive Binary Scatter plot.
    -   **N=3:** Interactive Ternary Diagram (1000x625px) with adjusted margins. Points are blue with black borders, rendered above the grid.
    -   **Formatting:** Axes labels always show 1 decimal place (e.g., 20.0).

    # Parameters (GUI Inputs)
    -   **Global:** Degree, Total Mass, Replicates.
    -   **Ingredients:** Select (for plot), Name, Purity (%), Max Active (%), Density (g/mL), Is Solvent.

    # Returns
    -   Interactive Widget Interface.
    -   Styled Data Table.
    -   Plotly Figures (Selective).
    -   **Excel Export (.xlsx):** File containing two sheets: 'Datapoints' (the design) and 'Parameters' (input settings).

    # Change Log
    -   **v70.7 (Dec/13/2025):**
        -   **Logic:** Implemented mass normalization for "No Solvent" scenarios. Now, if no solvent is selected, product masses are scaled to ensure `Sum Mass` = `Total Mass` and `Sum %` = 100%.
    -   **v70.6 (Dec/13/2025):**
        -   **Logic:** Enhanced `calculate_design` to explicitly report the detected Solvent.
    -   **v70.5 (Dec/13/2025):**
        -   **Environment:** Added `google.colab.output.enable_custom_widget_manager()`.
    -   **v70.4 (Dec/13/2025):**
        -   **UI:** Adjusted label widths for "Max Active" and "Density".
    -   **v70.3 (Dec/13/2025):**
        -   **Environment:** Added automatic detection of Google Colab widget manager.
    -   **v70.2 (Dec/13/2025):**
        -   **Architecture:** Internalized imports.
    -   **v70.1 (Dec/13/2025):**
        -   **Export:** Excel export support.

    # Test Example
    ```python
    simplex_lattice_design_v70_7()
    ```

    # Credits
    -   **Author:** Manazael Zuliani Jora
    -   **Date:** Dec/13/2025
