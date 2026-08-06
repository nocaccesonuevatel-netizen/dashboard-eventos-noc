# --------------------------------------------------------------------------
    # ÁREA: RED CORE
    # --------------------------------------------------------------------------
    else:
        st.subheader("🧠 Reporte Diario - RED CORE")

        if uploaded_matutino is not None:
            try:
                df_core_raw = pd.read_excel(uploaded_matutino)
                df_core_raw.columns = [str(c).strip() for c in df_core_raw.columns]

                # Identificar la columna de Cronología (por nombre o por posición P1 -> índice 15)
                col_crono = "CRONOLOGIA DEL EVENTO" if "CRONOLOGIA DEL EVENTO" in df_core_raw.columns else df_core_raw.columns[15]

                # Procesar columna de Fecha
                col_fecha = "FECHA INICIO" if "FECHA INICIO" in df_core_raw.columns else df_core_raw.columns[0]
                df_core_raw["Fecha_DT"] = pd.to_datetime(df_core_raw[col_fecha], dayfirst=True, errors="coerce")
                
                # Control de filtro por Fecha
                col_f1, col_f2 = st.columns([2, 1])
                filtrar_por_fecha = col_f2.checkbox("Filtrar por fecha", value=True)

                if filtrar_por_fecha and df_core_raw["Fecha_DT"].notna().any():
                    default_date_core = df_core_raw["Fecha_DT"].max().date()
                    selected_date_core = col_f1.date_input(
                        "📅 Selecciona la Fecha del Reporte CORE:",
                        value=default_date_core,
                        format="DD/MM/YYYY",
                        key="date_core"
                    )
                    df_core_filtered = df_core_raw[df_core_raw["Fecha_DT"].dt.date == selected_date_core]
                else:
                    df_core_filtered = df_core_raw.copy()

                # Campos de entrada manual
                st.markdown("---")
                col_c1, col_c2 = st.columns(2)
                alarmas_cortex = col_c1.text_input("Alarmas de CORTEX:", value="Ninguno")
                trabajos_prog_core = col_c2.text_input("Trabajos Programados (Core):", value="Ninguno")

                col_c3, col_c4, col_c5 = st.columns(3)
                roaming = col_c3.text_input("ROAMING:", value="Ninguno")
                hss_comfone = col_c4.text_input("HSS-COMFONE:", value="Ninguno")
                otros = col_c5.text_input("OTROS:", value="Ninguno")

                # Búsqueda flexible de palabras clave en CRONOLOGIA DEL EVENTO
                serie_crono = df_core_filtered[col_crono].dropna().astype(str)

                dwdm_list = serie_crono[serie_crono.str.contains("DWDM", case=False, na=False)].tolist()
                isp_list = serie_crono[serie_crono.str.contains("ISP", case=False, na=False)].tolist()
                # Busca 'INTERCONEXION' o 'INTERCONEXIÓN' con o sin tilde
                icx_list = serie_crono[serie_crono.str.contains("INTERCONEXI", case=False, na=False)].tolist()

                txt_dwdm = "\n".join([f"-{val.strip()}" for val in dwdm_list]) if dwdm_list else "-NINGUNO"
                txt_isp = "\n".join([f"-{val.strip()}" for val in isp_list]) if isp_list else "-Ninguno"
                txt_icx = "\n".join([f"-{val.strip()}" for val in icx_list]) if icx_list else "- Ninguno"

                # Generar Mensaje WhatsApp con negritas (*texto*)
                msg_core = (
                    f"Buenos dias Juanjo,\n\n"
                    f"*Eventos de consideración RED CORE:*\n"
                    f"-SIN EVENTOS\n\n"
                    f"*Eventos DWDM:*\n"
                    f"{txt_dwdm}\n\n"
                    f"*Eventos ISP:*\n"
                    f"{txt_isp}\n\n"
                    f"*Eventos ICX:*\n"
                    f"{txt_icx}\n\n"
                    f"*Alarmas de CORTEX:*\n"
                    f"-{alarmas_cortex}\n\n"
                    f"*Trabajos Programados:*\n"
                    f"-{trabajos_prog_core}\n\n"
                    f"*ROAMING:*\n"
                    f"-{roaming}\n\n"
                    f"*HSS-COMFONE:*\n"
                    f"-{hss_comfone}\n\n"
                    f"*OTROS:*\n"
                    f"-{otros}"
                )

                st.subheader("📲 Reporte para WhatsApp (RED CORE)")
                st.text_area("Copia el texto generado:", msg_core, height=380)

            except Exception as e:
                st.error(f"Error al procesar el archivo de CORE: {e}")
        else:
            st.info("👈 Por favor, carga el archivo Excel para generar automáticamente el reporte de RED CORE.")
