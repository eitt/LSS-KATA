import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import statsmodels.api as sm

# Initial Page Configuration
st.set_page_config(page_title="Lean Six Sigma Analytics", layout="wide")

# Sidebar navigation
st.sidebar.title("Navigation / Table of Contents")
pages = [
    "Introduction",
    "0. The Case Study",
    "1. Performance Summary",
    "2. Descriptive Statistics",
    "3. Statistical Process Control",
    "4. Root Cause Analysis"
]
page = st.sidebar.radio("Go to:", pages)

# ==========================================
# 1. DATA GENERATION (Simulation) - Global
# ==========================================
@st.cache_data
def generate_data():
    """
    Generates a synthetic dataset simulating a manufacturing process.
    Mathematical relationship: Diameter depends slightly on temperature.
    """
    np.random.seed(42)
    n_samples = 500
    
    # Input Variables (X)
    temperature = np.random.normal(loc=85, scale=5, size=n_samples) # Oven Temperature
    shift = np.random.choice(['Morning', 'Afternoon', 'Night'], size=n_samples)
    
    # Output Variable (Y) - Diameter (Target = 10.0 mm)
    noise = np.random.normal(loc=0, scale=0.15, size=n_samples)
    diameter = 10.0 + (temperature - 85) * 0.05 + noise
    
    # Create DataFrame
    df = pd.DataFrame({
        'Part_ID': range(1, n_samples + 1),
        'Shift': shift,
        'Temperature_C': temperature,
        'Diameter_mm': diameter
    })
    return df

df = generate_data()

# ==========================================
# 2. SIDEBAR CONTROLS & GLOBAL METRICS
# ==========================================
if page not in ["Introduction", "0. The Case Study"]:
    st.sidebar.header("Process Parameters")
    st.sidebar.markdown("Adjust customer limits and filter data to observe how metrics react.")

    # Filters
    selected_shift = st.sidebar.multiselect(
        "Filter by Shift:", 
        options=df['Shift'].unique(), 
        default=df['Shift'].unique()
    )

    # Specification Limits (USL / LSL)
    target = 10.0
    lsl = st.sidebar.number_input("Lower Spec Limit (LSL)", value=9.5, step=0.1)
    usl = st.sidebar.number_input("Upper Spec Limit (USL)", value=10.5, step=0.1)

    # Apply filters
    filtered_df = df[df['Shift'].isin(selected_shift)].copy()

    # Central tendency and dispersion measures
    mu = filtered_df['Diameter_mm'].mean()
    sigma = filtered_df['Diameter_mm'].std()

    # Capability Analysis
    cp = (usl - lsl) / (6 * sigma) if sigma > 0 else 0
    cpk_upper = (usl - mu) / (3 * sigma) if sigma > 0 else 0
    cpk_lower = (mu - lsl) / (3 * sigma) if sigma > 0 else 0
    cpk = min(cpk_upper, cpk_lower)

    # Defects and Sigma Level (DPMO Approximation)
    defects = filtered_df[(filtered_df['Diameter_mm'] > usl) | (filtered_df['Diameter_mm'] < lsl)].shape[0]
    dpmo = (defects / len(filtered_df)) * 1_000_000 if len(filtered_df) > 0 else 0
    
    if dpmo == 0:
        sigma_level = 6.0
    else:
        sigma_level = abs(stats.norm.ppf(defects / len(filtered_df))) + 1.5 


# ==============================================================================
# --- Page Routing ---
# ==============================================================================
if page == "Introduction":
    st.header("Welcome to Lean Six Sigma Statistical Analysis Module")
    
    st.markdown(
        """
        This interactive application is designed to provide a hands-on understanding of the core concepts in **Lean Six Sigma (LSS)** and data-driven process improvement. 
        
        We will build intuition for how to measure, analyze, and improve industrial processes by exploring a practical case study. You will apply these concepts using fundamental statistical tools, ranging from descriptive statistics to root cause regression analysis.
        
        ### Table of Contents
        0. **The Case Study**: Discover the manufacturing challenge we are trying to solve.
        1. **Performance Summary**: Baseline the current process using key metrics like Mean, Standard Deviation, Cpk, and Sigma Level.
        2. **Descriptive Statistics**: Visualize process distribution versus customer specifications using histograms and box plots.
        3. **Statistical Process Control**: Evaluate process stability over time using X Control Charts.
        4. **Root Cause Analysis**: Use correlation and linear regression to identify the impact of variables on the process output.
        
        Use the sidebar to navigate through the modules.
        """
    )
    
    st.subheader("About the Author")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        try:
            st.image("photo.png")
        except FileNotFoundError:
            st.error("Profile image not found. Make sure 'photo.png' is in your repo.")

    with col2:
        st.markdown(
            """
            **Leonardo H. Talero-Sarmiento** holds a Ph.D. in Engineering from the Universidad Autónoma de Bucaramanga. 
            He spends his time exploring how mathematical modeling, data analytics, and operations research can solve 
            real-world problems. 
            
            Whether he's working on improving manufacturing systems or figuring out better ways to adopt new technologies, 
            his focus is always on making processes work better. Much of his research looks at decision-making in both 
            agriculture and industry—finding ways to make supply chains more resilient, optimize healthcare delivery, 
            and help organizations embrace digital transformation.
            
            Over the years, he has contributed extensively to the academic community, publishing 46 papers in journals 
            like *Heliyon*, *AgriEngineering*, and *Digital Policy, Regulation and Governance*. He also stays highly active 
            as a peer reviewer, having completed over 44 reviews for publications such as *Agriculture*, *Applied Sciences*, 
            and *Digital Transformation and Society*.
            """
        )

elif page == "0. The Case Study":
    st.title("The Challenge: High Defect Rates in Precision Shafts")
    
    st.markdown("""
    ### Background
    A precision engineering plant produces metal shafts for automotive engines. The critical quality characteristic is the **shaft diameter**, which has a strict target of **10.0 mm**, with allowable limits of **9.5 mm (LSL)** to **10.5 mm (USL)**.
    
    ### The Problem
    Recently, customers have been rejecting shipments because a significant portion of the shafts fall outside these specification limits. This is costing the company money in scrap, rework, and customer dissatisfaction.
    
    ### Potential Suspects
    The engineering team suspects two potential root causes for the variation in diameter:
    1. **Oven Temperature**: The metal shafts undergo a heat treatment process. Does fluctuations in the oven temperature affect the final diameter?
    2. **Shift Differences**: Does the quality vary depending on whether the part was produced during the Morning, Afternoon, or Night shift?
    
    ### Your Mission
    Use the Lean Six Sigma tools in the following tabs to:
    1. **Measure** the current capability of the process.
    2. **Analyze** if the process is statistically stable over time.
    3. **Determine** if oven temperature is the root cause of the diameter variation.
    """)

elif page == "1. Performance Summary":
    st.title("1. Performance Summary")
    st.markdown("""
    **Case Study Context:** Before making any changes, we must baseline the current capability of our shaft production. Are we meeting customer expectations? 
    We use the **Cpk** (Process Capability Index) and **Sigma Level** to measure how well our process fits within the customer's limits (9.5 to 10.5 mm).
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean (μ)", f"{mu:.3f} mm")
    col2.metric("Std Dev. (σ)", f"{sigma:.3f} mm")
    col3.metric("Cpk Index", f"{cpk:.2f}", delta="Poor (<1.33)" if cpk < 1.33 else "Capable (>1.33)", delta_color="inverse")
    col4.metric("Sigma Level", f"{sigma_level:.1f} σ")

    st.markdown("### Step-by-Step Calculations")
    
    st.markdown("#### 1. Mean (μ) and Standard Deviation (σ)")
    st.latex(r"\mu = \frac{\sum x_i}{N} \quad ; \quad \sigma = \sqrt{\frac{\sum (x_i - \mu)^2}{N-1}}")
    st.latex(rf"\mu = {mu:.3f} \text{{ mm}} \quad ; \quad \sigma = {sigma:.3f} \text{{ mm}}")
    
    st.markdown("#### 2. Process Capability Index (Cpk)")
    st.markdown("Cpk penalizes the score if the process mean is not perfectly centered between the specification limits.")
    st.latex(r"Cpk = \min \left( \frac{USL - \mu}{3\sigma}, \frac{\mu - LSL}{3\sigma} \right)")
    st.latex(rf"Cpk = \min \left( \frac{{{usl} - {mu:.3f}}}{{3 \times {sigma:.3f}}}, \frac{{{mu:.3f} - {lsl}}}{{3 \times {sigma:.3f}}} \right)")
    st.latex(rf"Cpk = \min ({cpk_upper:.2f}, {cpk_lower:.2f}) = {cpk:.2f}")
    
    st.markdown("#### 3. Sigma Level (Approximation via DPMO)")
    st.latex(r"DPMO = \left( \frac{\text{Defects}}{\text{Total Opportunities}} \right) \times 1,000,000")
    st.latex(rf"DPMO = \left( \frac{{{defects}}}{{{len(filtered_df)}}} \right) \times 1,000,000 = {dpmo:.1f}")
    st.latex(r"Z_{score} = \Phi^{-1}\left(\frac{\text{Defects}}{N}\right)")
    st.latex(r"\text{Sigma Level} = |Z_{score}| + 1.5 \text{ (shift)}")
    st.latex(rf"\text{Sigma Level} = {sigma_level:.1f} \sigma")

elif page == "2. Descriptive Statistics":
    st.title("2. Descriptive Statistics")
    st.markdown("""
    **Case Study Context:** We need to visually compare the **Voice of the Process** (how the shaft diameters are actually distributed) against the **Voice of the Customer** (the red LSL and USL lines). 
    A histogram allows us to quickly see if our production is centered around the 10.0 mm target and if the tails of the bell curve spill over the rejection limits.
    """)

    fig_hist = px.histogram(
        filtered_df, x='Diameter_mm', 
        nbins=30, 
        marginal='box', 
        color_discrete_sequence=['#1f77b4'],
        opacity=0.7
    )
    fig_hist.add_vline(x=lsl, line_dash="dash", line_color="red", annotation_text="LSL")
    fig_hist.add_vline(x=usl, line_dash="dash", line_color="red", annotation_text="USL")
    fig_hist.add_vline(x=target, line_dash="solid", line_color="green", annotation_text="Target")

    fig_hist.update_layout(xaxis_title="Diameter (mm)", yaxis_title="Frequency", template="plotly_white")
    st.plotly_chart(fig_hist, use_container_width=True)

elif page == "3. Statistical Process Control":
    st.title("3. Statistical Process Control")
    st.markdown("""
    **Case Study Context:** Is the variation in our shaft diameter predictable (Common Cause) or erratic (Special Cause)? 
    We plot the diameters sequentially over time on an X-chart. If points fall outside the Control Limits (UCL/LCL), it indicates a sudden, assignable disruption in the process that must be investigated.
    """)

    ucl = mu + (3 * sigma)
    lcl = mu - (3 * sigma)

    st.markdown("### Step-by-Step Calculations")
    st.markdown("Control limits are defined by the natural variation of the process ($\pm 3\sigma$), NOT by the customer's limits.")
    st.latex(r"UCL = \mu + 3\sigma \quad ; \quad LCL = \mu - 3\sigma")
    st.latex(rf"UCL = {mu:.3f} + 3({sigma:.3f}) = {ucl:.3f}")
    st.latex(rf"LCL = {mu:.3f} - 3({sigma:.3f}) = {lcl:.3f}")

    fig_spc = go.Figure()
    fig_spc.add_trace(go.Scatter(x=filtered_df['Part_ID'], y=filtered_df['Diameter_mm'], 
                                 mode='lines+markers', name='Diameter', marker=dict(size=5, color='gray')))
    fig_spc.add_trace(go.Scatter(x=filtered_df['Part_ID'], y=[mu]*len(filtered_df), 
                                 mode='lines', name='Mean (CL)', line=dict(color='blue', width=2)))
    fig_spc.add_trace(go.Scatter(x=filtered_df['Part_ID'], y=[ucl]*len(filtered_df), 
                                 mode='lines', name='UCL (+3σ)', line=dict(color='orange', dash='dash')))
    fig_spc.add_trace(go.Scatter(x=filtered_df['Part_ID'], y=[lcl]*len(filtered_df), 
                                 mode='lines', name='LCL (-3σ)', line=dict(color='orange', dash='dash')))

    outliers_spc = filtered_df[(filtered_df['Diameter_mm'] > ucl) | (filtered_df['Diameter_mm'] < lcl)]
    fig_spc.add_trace(go.Scatter(x=outliers_spc['Part_ID'], y=outliers_spc['Diameter_mm'], 
                                 mode='markers', name='Special Cause', marker=dict(size=10, color='red', symbol='x')))

    fig_spc.update_layout(xaxis_title="Production Sequence (Part ID)", yaxis_title="Diameter (mm)", template="plotly_white")
    st.plotly_chart(fig_spc, use_container_width=True)

elif page == "4. Root Cause Analysis":
    st.title("4. Root Cause Analysis")
    st.markdown("""
    **Case Study Context:** The engineering team suspects the heat treatment oven temperature (X) is causing the shaft diameter (Y) to expand unpredictably.
    We will use Pearson Correlation ($r$) and Linear Regression to mathematically prove or disprove this hypothesis.
    """)

    col_scatter, col_stats = st.columns([2, 1])

    with col_scatter:
        fig_scatter = px.scatter(
            filtered_df, x='Temperature_C', y='Diameter_mm', 
            color='Shift', trendline='ols',
            title="Scatter: Temperature vs Diameter",
            opacity=0.6,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_scatter.update_layout(template="plotly_white")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_stats:
        st.markdown("#### Model Findings")
        correlation, p_value = stats.pearsonr(filtered_df['Temperature_C'], filtered_df['Diameter_mm'])
        
        st.write(f"**Correlation Coefficient (r):** {correlation:.2f}")
        if abs(correlation) > 0.7:
            st.success("Strong Correlation detected.")
        elif abs(correlation) > 0.3:
            st.warning("Moderate Correlation detected.")
        else:
            st.info("Weak Correlation.")
            
        st.write(f"**P-value:** {p_value:.4f}")
        if p_value < 0.05:
            st.success("The relationship is statistically significant (Reject H0).")
        else:
            st.error("Not enough evidence of relationship (Accept H0).")
            
        st.info("Conclusion: If the regression is significant, controlling the oven temperature is a vital root cause to reduce diameter variation and improve the Sigma Level.")

    st.markdown("### Step-by-Step Calculations")
    st.markdown("#### 1. Pearson Correlation Coefficient ($r$)")
    st.latex(r"r = \frac{\sum(x_i-\bar{x})(y_i-\bar{y})}{\sqrt{\sum(x_i-\bar{x})^2 \sum(y_i-\bar{y})^2}}")
    st.latex(rf"r = {correlation:.3f}")
    
    st.markdown("#### 2. Hypothesis Testing (P-value)")
    st.markdown("We test if the slope of our regression line is significantly different from zero.")
    st.latex(r"H_0: \beta_1 = 0 \quad (\text{No relationship})")
    st.latex(r"H_1: \beta_1 \neq 0 \quad (\text{Relationship exists})")
    st.latex(rf"\text{{P-value}} = {p_value:.4f}")
    
    if p_value < 0.05:
        st.markdown(rf"Because $P < 0.05$, we **reject $H_0$**. Temperature explains a significant portion of the variance in Diameter.")
    else:
        st.markdown(rf"Because $P \ge 0.05$, we **fail to reject $H_0$**. Temperature does not explain the variance in Diameter.")