import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# Initial Page Configuration
st.set_page_config(page_title="Lean Six Sigma Analytics", layout="wide")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Introduction", "Analytics Dashboard"])

# ==============================================================================
# --- Page 1: Introduction ---
# ==============================================================================
if page == "Introduction":
    st.header("Welcome to the Supervised Learning App")
    
    st.markdown(
        """
        This interactive application is designed to provide a hands-on understanding of
        the core concepts in supervised machine learning. 
        
        We will build intuition for how models "learn" by exploring optimization,
        and then apply these concepts to fundamental models for both regression and classification.
        
        Use the sidebar to navigate through the modules.
        """
    )
    
    st.subheader("About the Author")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # --- FIX: Changed to photo.png as requested ---
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

# ==============================================================================
# --- Page 2: Analytics Dashboard ---
# ==============================================================================
elif page == "Analytics Dashboard":
    # ==========================================
    # 1. DATA GENERATION (Simulation)
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
        # Relationship: higher temperature, larger diameter + random noise
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
    # 2. SIDEBAR: REACTIVE CONTROLS
    # ==========================================
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

    # ==========================================
    # 3. STATISTICAL CALCULATIONS LOGIC
    # ==========================================
    # Central tendency and dispersion measures
    mu = filtered_df['Diameter_mm'].mean()
    sigma = filtered_df['Diameter_mm'].std()

    # Capability Analysis
    # Cp = Tolerance / Process Variation
    cp = (usl - lsl) / (6 * sigma) if sigma > 0 else 0
    # Cpk = Penalizes if the mean is not centered
    cpk_upper = (usl - mu) / (3 * sigma) if sigma > 0 else 0
    cpk_lower = (mu - lsl) / (3 * sigma) if sigma > 0 else 0
    cpk = min(cpk_upper, cpk_lower)

    # Defects and Sigma Level (DPMO Approximation)
    defects = filtered_df[(filtered_df['Diameter_mm'] > usl) | (filtered_df['Diameter_mm'] < lsl)].shape[0]
    dpmo = (defects / len(filtered_df)) * 1_000_000 if len(filtered_df) > 0 else 0
    # Approximate Sigma Level (using inverse standard normal + 1.5 shift)
    if dpmo == 0:
        sigma_level = 6.0
    else:
        # stats.norm.ppf calculates the normal quantile
        sigma_level = abs(stats.norm.ppf(defects / len(filtered_df))) + 1.5 

    # ==========================================
    # 4. APPLICATION BODY (STORYTELLING)
    # ==========================================
    st.title("Lean Six Sigma Analytics Assistant")
    st.markdown("""
    Welcome to the interactive process analysis. This tool transforms raw data into **actionable knowledge**. 
    We will navigate from a basic understanding of our production to root cause identification.
    """)

    # --- SECTION A: Main KPIs ---
    st.markdown("### 1. Performance Summary (Key Metrics)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean (μ)", f"{mu:.3f} mm")
    col2.metric("Std Dev. (σ)", f"{sigma:.3f} mm")
    col3.metric("Cpk Index", f"{cpk:.2f}", delta="Poor (<1.33)" if cpk < 1.33 else "Capable (>1.33)", delta_color="inverse")
    col4.metric("Sigma Level", f"{sigma_level:.1f} σ")

    st.divider()

    # --- SECTION B: Descriptive Statistics ---
    st.markdown("### 2. Process Distribution vs. Customer")
    st.markdown("We visualize the **Voice of the Process** (Histogram) against the **Voice of the Customer** (Red Lines LSL/USL).")

    fig_hist = px.histogram(
        filtered_df, x='Diameter_mm', 
        nbins=30, 
        marginal='box', # Adds a Boxplot on top to identify outliers
        color_discrete_sequence=['#1f77b4'],
        opacity=0.7
    )
    # Add specification lines
    fig_hist.add_vline(x=lsl, line_dash="dash", line_color="red", annotation_text="LSL")
    fig_hist.add_vline(x=usl, line_dash="dash", line_color="red", annotation_text="USL")
    fig_hist.add_vline(x=target, line_dash="solid", line_color="green", annotation_text="Target")

    fig_hist.update_layout(xaxis_title="Diameter (mm)", yaxis_title="Frequency", template="plotly_white")
    st.plotly_chart(fig_hist, use_container_width=True)

    st.divider()

    # --- SECTION C: Statistical Process Control (SPC) ---
    st.markdown("### 3. Statistical Process Control (X Control Chart)")
    st.markdown("Are there any special causes of variation? We evaluate the temporal stability of the process.")

    # Calculations for Control Chart (Simple approximation with Mean +/- 3 Sigma)
    ucl = mu + (3 * sigma)
    lcl = mu - (3 * sigma)

    fig_spc = go.Figure()
    # Process data
    fig_spc.add_trace(go.Scatter(x=filtered_df['Part_ID'], y=filtered_df['Diameter_mm'], 
                                 mode='lines+markers', name='Diameter', marker=dict(size=5, color='gray')))
    # Center line
    fig_spc.add_trace(go.Scatter(x=filtered_df['Part_ID'], y=[mu]*len(filtered_df), 
                                 mode='lines', name='Mean (CL)', line=dict(color='blue', width=2)))
    # Control limits
    fig_spc.add_trace(go.Scatter(x=filtered_df['Part_ID'], y=[ucl]*len(filtered_df), 
                                 mode='lines', name='UCL (+3σ)', line=dict(color='orange', dash='dash')))
    fig_spc.add_trace(go.Scatter(x=filtered_df['Part_ID'], y=[lcl]*len(filtered_df), 
                                 mode='lines', name='LCL (-3σ)', line=dict(color='orange', dash='dash')))

    # Highlight out-of-control points (Simple Nelson Rule 1)
    outliers_spc = filtered_df[(filtered_df['Diameter_mm'] > ucl) | (filtered_df['Diameter_mm'] < lcl)]
    fig_spc.add_trace(go.Scatter(x=outliers_spc['Part_ID'], y=outliers_spc['Diameter_mm'], 
                                 mode='markers', name='Special Cause', marker=dict(size=10, color='red', symbol='x')))

    fig_spc.update_layout(xaxis_title="Production Sequence (Part ID)", yaxis_title="Diameter (mm)", template="plotly_white")
    st.plotly_chart(fig_spc, use_container_width=True)

    st.divider()

    # --- SECTION D: Relationship Analysis (Regression) ---
    st.markdown("### 4. Root Cause Analysis (Variable Relationships)")
    st.markdown("Through correlation analysis and linear regression, we evaluate how **Temperature** (X) impacts the **Diameter** (Y).")

    col_scatter, col_stats = st.columns([2, 1])

    with col_scatter:
        # Scatter plot with trendline (Ordinary Least Squares OLS Regression)
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
        # Calculate Pearson Correlation
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
            st.success("The relationship is **statistically significant** (Reject H0).")
        else:
            st.error("Not enough evidence of relationship (Accept H0).")
            
        st.info("Conclusion: If the regression is significant, controlling the oven temperature is a vital root cause to reduce diameter variation and improve the Sigma Level.")