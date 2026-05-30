# --------------------------------------------------------------------------
    # TAB 5: ADVANCED - CAVITACIÓN Y NÚMERO DE REYNOLDS (ESTRUCTURADO)
    # --------------------------------------------------------------------------
    with tab5:
        st.subheader("🧼 Análisis Hidrodinámico Avanzado: Mecánica de Fluidos")
        
        # Cálculos base
        v_m_s = velocidad * 0.514444
        v_avance = v_m_s * (1.0 - estela)
        n_rps = rpm_motor / 60.0
        radius_07 = 0.7 * (diam_prop_m / 2.0)
        v_tangencial = 2.0 * math.pi * n_rps * radius_07
        v_relativa_07 = math.sqrt(v_avance**2 + v_tangencial**2)
        cuerda_07 = (1.5 * diam_prop_m * ae_val) / z_val
        viscosidad_cinematica = 1.188e-6
        reynolds_n = (v_relativa_07 * cuerda_07) / viscosidad_cinematica
        
        # --- SECCIÓN 1: RÉGIMEN DE REYNOLDS ---
        st.markdown("---")
        st.markdown("### 🧪 1. Análisis del Régimen de Flujo (Número de Reynolds)")
        
        # Diagnóstico Reynolds
        if reynolds_n > 2e5:
            st.markdown("""<div class="status-box-safe">🟢 <b>RÉGIMEN ESTABLE:</b> El número de Reynolds calculado indica flujo turbulento desarrollado, cumpliendo con los estándares de la ITTC para modelos de hélice.</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="status-box-danger">❌ <b>ALERTA DE FLUJO:</b> El número de Reynolds es bajo; se espera un flujo laminar/transicional que puede alterar la precisión de los coeficientes.</div>""", unsafe_allow_html=True)

        col_r1, col_r2 = st.columns([1, 1.5])
        with col_r1:
            st.metric("Número de Reynolds ($R_n$ en $0.7r$)", f"{reynolds_n:.2e}")
        with col_r2:
            # Gráfica Reynolds
            velocidades_nudos = np.linspace(1, 22, 100)
            reynolds_curva = []
            for v_kn in velocidades_nudos:
                v_ms_i = v_kn * 0.514444
                v_va_i = v_ms_i * (1.0 - estela)
                v_rel_i = math.sqrt(v_va_i**2 + v_tangencial**2)
                rn_i = (v_rel_i * cuerda_07) / viscosidad_cinematica
                reynolds_curva.append(rn_i)
            
            fig_rn, ax_rn = plt.subplots(figsize=(6, 3))
            ax_rn.plot(velocidades_nudos, reynolds_curva, color='#4c1d95', lw=2)
            ax_rn.axvline(x=velocidad, color='#10b981', linestyle='--')
            ax_rn.axhline(y=2e5, color='#ef4444', linestyle=':')
            ax_rn.set_ylabel('$R_n$'); ax_rn.set_xlabel('Velocidad (kts)')
            st.pyplot(fig_rn)

        # --- SECCIÓN 2: CAVITACIÓN ---
        st.markdown("---")
        st.markdown("### 🧼 2. Análisis de Cavitación (Keller & Burrill)")
        
        # Cálculos adicionales
        p_atmosferica = 101325.0
        p_vapor = 1705.0
        densidad_agua = 1025.0
        p_hidrostatica = p_atmosferica + (densidad_agua * 9.81 * inmersion_eje_m) - p_vapor
        eta_open_water = 0.55
        empuje_t_n = (potencia_kw * 1000.0 * eta_open_water) / (v_avance if v_avance > 0 else 1.0)
        ae_ao_keller = ((1.3 + 0.3 * z_val) * empuje_t_n) / (p_hidrostatica * (diam_prop_m**2)) + 0.03
        ap_area = ae_val * (math.pi * (diam_prop_m**2) / 4.0) * (1.067 - 0.229 * pd_val)
        q_dinamica_07 = 0.5 * densidad_agua * (v_relativa_07**2)
        tau_c_diseno = empuje_t_n / (ap_area * q_dinamica_07)
        sigma_07_diseno = p_hidrostatica / q_dinamica_07

        # Diagnóstico Cavitación
        if ae_val >= ae_ao_keller:
            st.markdown("""<div class="status-box-safe">🟢 <b>DISEÑO PROTEGIDO:</b> El Área Expandida (Ae/Ao) es suficiente para evitar la cavitación por empuje según el criterio de Keller.</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="status-box-danger">❌ <b>RIESGO DE CAVITACIÓN:</b> El área de las palas es insuficiente. Se recomienda aumentar el Ae/Ao.</div>""", unsafe_allow_html=True)
            
        col_c1, col_c2 = st.columns([1, 1.5])
        with col_c1:
            st.metric("Área Expandida Mínima (Keller)", f"{ae_ao_keller:.3f}")
            st.metric("Tu Área Expandida", f"{ae_val:.3f}")
        with col_c2:
            # Gráfica Burrill
            fig_burrill, ax_b = plt.subplots(figsize=(6, 3))
            sigma_axis = np.linspace(0.1, 1.5, 200)
            tau_limite_burrill = 0.30 * (sigma_axis**0.68)
            ax_b.plot(sigma_axis, tau_limite_burrill, color='#ef4444', lw=2)
            ax_b.fill_between(sigma_axis, tau_limite_burrill, 1.5, color='#ef4444', alpha=0.1)
            ax_b.scatter([sigma_07_diseno], [tau_c_diseno], color='#ca8a04', s=100)
            ax_b.set_xlabel('Número de Cavitación ($\sigma_{0.7R}$)')
            ax_b.set_ylabel('Coef. Empuje ($\tau_C$)')
            st.pyplot(fig_burrill)
