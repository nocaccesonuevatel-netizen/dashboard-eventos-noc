import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Gestión de Eventos y Reportes NOC", page_icon="🚨", layout="wide")

# ==============================================================================
# NAVEGACIÓN PRINCIPAL ENTRE MÓDULOS (PESTAÑAS)
# ==============================================================================
tab_pendientes, tab_matutino = st.tabs([
    "📋 1. Reporte Eventos Pendientes", 
    "🌅 2. Reporte Matutino (Diario)"
])

# ==============================================================================
# MÓDULO 1: REPORTE DE EVENTOS PENDIENTES
# ==============================================================================
with tab_pendientes:
    st.title("🚨 Gestión y Reporte de Eventos Pendientes")

    uploaded_file = st.sidebar.file_uploader("Cargar Excel (Pendientes)", type=["xlsx", "xls"], key="uploader_pendientes")

    if uploaded_file is not None:
        try:
            df_raw = pd.read_excel(uploaded_file)
            
            # Limpiar espacios en los nombres de columnas
            df_raw.columns = [str(col).strip() for col in df_raw.columns]
            
            # Identificar la columna AG (posición 32 de base 0, la 33ª columna)
            col_ag_nombre = None
            if len(df_raw.columns) >= 33:
                col_ag_nombre = df_raw.columns[32]
            
            # Columnas requeridas (sin SERVICIOS AFECTADOS, incluyendo CRONOLOGIA DEL EVENTO)
            columnas_deseadas = [
                "FECHA INICIO", "HORA INICIO", "IMPACTO", "ZONA AFECTADA", 
                "CIUDAD", "CELL ID", "TECNOLOGIAS AFECTADAS", 
                "CAUSA PRELIMINAR", "CRONOLOGIA DEL EVENTO"
            ]
            
            cols_existentes = [col for col in columnas_deseadas if col in df_raw.columns]
            
            if "FECHA INICIO" not in df_raw.columns or "CIUDAD" not in df_raw.columns:
                st.error("❌ Faltan columnas principales. Asegúrate de incluir 'FECHA INICIO' y 'CIUDAD'.")
                st.write("Columnas detectadas:", list(df_raw.columns))
            else:
                df = df_raw.copy()

                # --- FILTRO POR ESTADO (COLUMNA AG == PENDIENTE) ---
                if col_ag_nombre:
                    df = df[df[col_ag_nombre].astype(str).str.strip().str.upper() == "PENDIENTE"]
                # --------------------------------------------------

                # Procesamiento de Fechas
                df["Fecha_DT"] = pd.to_datetime(df["FECHA INICIO"], dayfirst=True, errors="coerce")
                df = df.dropna(subset=["Fecha_DT"])

                df["Año"] = df["Fecha_DT"].dt.year

                # --- FILTRO AUTOMÁTICO: AÑO 2026 EN ADELANTE ---
                df = df[df["Año"] >= 2026]

                # Barra Lateral - Filtros por Fecha de Inicio y Ciudad
                st.sidebar.header("🔍 Filtros (Pendientes)")

                min_f = df["Fecha_DT"].min().date() if not df.empty else datetime.date(2026, 1, 1)
                max_f = df["Fecha_DT"].max().date() if not df.empty else datetime.date(2030, 12, 31)

                selected_date = st.sidebar.date_input(
                    "Mostrar eventos desde la fecha:",
                    value=min_f,
                    min_value=datetime.date(2026, 1, 1),
                    max_value=max_f,
                    format="DD/MM/YYYY",
                    key="date_pendientes"
                )

                # Selector de Ciudad
                ciudades_opt = sorted(df["CIUDAD"].dropna().astype(str).unique())
                selected_ciudades = st.sidebar.multiselect("Ciudad", options=ciudades_opt, default=ciudades_opt, key="ciudades_pend")

                # --- APLICAR FILTRO: DESDE LA FECHA SELECCIONADA EN ADELANTE (>=) Y CIUDAD ---
                mask = (df["Fecha_DT"].dt.date >= selected_date) & (df["CIUDAD"].isin(selected_ciudades))
                df_filtered = df[mask]

                # Visualización KPIs y Tabla
                st.subheader("📊 Resumen General")
                col1, col2 = st.columns(2)
                col1.metric("Total Eventos Pendientes", len(df_filtered))

                if not df_filtered.empty and "IMPACTO" in df_filtered.columns:
                    desglose = df_filtered["IMPACTO"].value_counts().to_dict()
                    texto_impacto = " | ".join([f"**{k}:** {v}" for k, v in desglose.items()])
                    col2.markdown(f"**Desglose por Impacto:**\n\n{texto_impacto}")

                st.markdown("---")
                st.subheader("📋 Detalle de Eventos Filtrados")
                
                cols_tabla = [c for c in cols_existentes if c in df_filtered.columns]
                df_display = df_filtered[cols_tabla].copy()
                df_display["FECHA INICIO"] = df_filtered["Fecha_DT"].dt.strftime("%d-%m-%Y")
                st.dataframe(df_display, use_container_width=True, hide_index=True)

                # Módulo WhatsApp
                st.markdown("---")
                st.subheader("📲 Reporte para WhatsApp")

                if not df_filtered.empty:
                    lineas_reporte = []
                    lineas_reporte.append("🚨 *REPORTE DE EVENTOS PENDIENTES* 🚨")
                    lineas_reporte.append(f"📊 *Total Pendientes:* {len(df_filtered)}\n")

                    col_crono_pend = "CRONOLOGIA DEL EVENTO" if "CRONOLOGIA DEL EVENTO" in df_filtered.columns else None

                    for ciudad, grupo in df_filtered.groupby("CIUDAD"):
                        lineas_reporte.append(f"📍 *CIUDAD: {str(ciudad).upper()}* ({len(grupo)})")
                        
                        for idx, row in grupo.iterrows():
                            fecha_str = row["Fecha_DT"].strftime("%d/%m/%Y")
                            causa = row.get("CAUSA PRELIMINAR", "N/A")
                            
                            lineas_reporte.append(f"🗓️ *Fecha:* {fecha_str}")
                            lineas_reporte.append(f"🔍 *Causa:* {causa}")

                            if col_crono_pend and pd.notna(row[col_crono_pend]):
                                texto_crono = str(row[col_crono_pend])
                                lineas_crono = texto_crono.split("\n")
                                
                                crono_filtrada = []
                                for linea in lineas_crono:
                                    linea_upper = linea.upper()
                                    if ("INICIO" in linea_upper or "CONTINUA" in linea_upper) and "FIN" not in linea_upper:
                                        crono_filtrada.append(f"  └ 📝 {linea.strip()}")
                                
                                if crono_filtrada:
                                    lineas_reporte.append("⏱️ *Cronología:*")
                                    lineas_reporte.extend(crono_filtrada)

                            lineas_reporte.append("")

                    texto_whatsapp = "\n".join(lineas_reporte)
                    st.text_area("Copia el siguiente texto para enviarlo por WhatsApp:", texto_whatsapp, height=350, key="txt_wa_pend")
                else:
                    st.warning("No hay eventos pendientes desde la fecha seleccionada para las ciudades elegidas.")

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    else:
        st.info("👈 Por favor, carga el archivo Excel en la barra lateral.")

# ==============================================================================
# MÓDULO 2: REPORTE MATUTINO (RED ACCESO Y RED CORE)
# ==============================================================================
with tab_matutino:
    st.title("🌅 Reporte Matutino Diario")

    area_turno = st.radio("Selecciona tu Área de Turno:", ["RED ACCESO", "RED CORE"], horizontal=True)
    st.markdown("---")

    uploaded_matutino = st.file_uploader(f"Cargar Excel ({area_turno})", type=["xlsx", "xls"], key="uploader_matutino")

    if area_turno == "RED ACCESO":
        st.subheader("📡 Reporte Diario - RED ACCESO")
        
        col_m1, col_m2 = st.columns(2)
        venc_credito = col_m1.text_input("Vencimiento crédito (Línea Tigo):", value="20/09/26")
        pru_cel = col_m2.text_input("Estado celulares de prueba:", value="Ambos cargando y con normalidad.")
        
        col_m3, col_m4 = st.columns(2)
        lineas_fij = col_m3.text_input("Estado líneas fijas:", value="Ambos con tono de linea")
        trabajos_prog_acc = col_m4.text_input("Trabajos programados (Acceso):", value="Ninguno")

        if uploaded_matutino is not None:
            try:
                df_acc = pd.read_excel(uploaded_matutino)
                df_acc.columns = [str(c).strip() for c in df_acc.columns]
                
                col_crit = df_acc.columns[4] if len(df_acc.columns) >= 5 else "CRITICIDAD"
                col_crono = df_acc.columns[15] if len(df_acc.columns) >= 16 else "CRONOLOGIA DEL EVENTO"

                col_fecha_acc = df_acc.columns[2] if len(df_acc.columns) >= 3 else df_acc.columns[0]
                df_acc["Fecha_Formateada"] = pd.to_datetime(df_acc[col_fecha_acc], dayfirst=True, errors="coerce").dt.strftime("[%d/%m/%Y]")
                df_acc["Fecha_Formateada"] = df_acc["Fecha_Formateada"].fillna("")

                df_criticos = df_acc[df_acc[col_crit].astype(str).str.strip().str.upper() == "ALTA"]
                df_mayores = df_acc[df_acc[col_crit].astype(str).str.strip().str.upper() == "MEDIA"]

                txt_criticos = "\n".join([f"-{row['Fecha_Formateada']} {row[col_crono]}" for _, row in df_criticos.iterrows() if pd.notna(row[col_crono])]) if not df_criticos.empty else "-NINGUNO"
                txt_mayores = "\n".join([f"-{row['Fecha_Formateada']} {row[col_crono]}" for _, row in df_mayores.iterrows() if pd.notna(row[col_crono])]) if not df_mayores.empty else "-NINGUNO"

                msg_acc = (
                    f"Buenos dias Juanjo,\n\n"
                    f"*Eventos de consideración RED ACCESO*\n"
                    f"*Eventos Críticos*\n"
                    f"{txt_criticos}\n\n"
                    f"*Eventos Mayores*\n"
                    f"{txt_mayores}\n\n"
                    f"*Estado Celular(linea Tigo) lado acceso*\n"
                    f" - Cargado, fecha de vencimiento de crédito {venc_credito}\n\n"
                    f"*Estado de celulares de prueba*\n"
                    f" - {pru_cel}\n\n"
                    f"*Estado líneas fijas*\n"
                    f" - {lineas_fij}\n\n"
                    f"*Trabajos programados*\n"
                    f"-{trabajos_prog_acc}"
                )

                st.subheader("📲 Reporte para WhatsApp (RED ACCESO)")
                st.text_area("Copia el texto generado:", msg_acc, height=350)

            except Exception as e:
                st.error(f"Error al procesar el archivo de ACCESO: {e}")
        else:
            st.info("👈 Por favor, carga el archivo Excel para generar automáticamente el reporte de RED ACCESO.")

    else:
        st.subheader("🧠 Reporte Diario - RED CORE")

        if uploaded_matutino is not None:
            try:
                df_core_raw = pd.read_excel(uploaded_matutino)
                df_core_raw.columns = [str(c).strip() for c in df_core_raw.columns]

                col_fecha_c1 = df_core_raw.columns[2] if len(df_core_raw.columns) >= 3 else df_core_raw.columns[0]
                df_core_raw["Fecha_DT"] = pd.to_datetime(df_core_raw[col_fecha_c1], dayfirst=True, errors="coerce")
                
                df_core_raw["Fecha_Texto"] = df_core_raw["Fecha_DT"].dt.strftime("[%d/%m/%Y]")
                df_core_raw["Fecha_Texto"] = df_core_raw["Fecha_Texto"].fillna("")

                col_f1, col_f2 = st.columns([2, 1])
                filtrar_por_fecha = col_f2.checkbox("Filtrar por fecha", value=True)

                if filtrar_por_fecha and df_core_raw["Fecha_DT"].notna().any():
                    min_fecha = df_core_raw["Fecha_DT"].min().date()
                    max_fecha = df_core_raw["Fecha_DT"].max().date()
                    
                    selected_date_core = col_f1.date_input(
                        "📅 Mostrar eventos desde la Fecha (Columna C1):",
                        value=min_fecha,
                        min_value=min_fecha,
                        max_value=max_fecha,
                        format="DD/MM/YYYY",
                        key="date_core_cal"
                    )
                    
                    df_core_filtered = df_core_raw[df_core_raw["Fecha_DT"].dt.date >= selected_date_core]
                else:
                    df_core_filtered = df_core_raw.copy()

                st.markdown("---")
                col_c1, col_c2 = st.columns(2)
                alarmas_cortex = col_c1.text_input("Alarmas de CORTEX:", value="Ninguno")
                trabajos_prog_core = col_c2.text_input("Trabajos Programados (Core):", value="Ninguno")

                col_c3, col_c4, col_c5 = st.columns(3)
                roaming = col_c3.text_input("ROAMING:", value="Ninguno")
                hss_comfone = col_c4.text_input("HSS-COMFONE:", value="Ninguno")
                otros = col_c5.text_input("OTROS:", value="Ninguno")

                col_crono = "CRONOLOGIA DEL EVENTO" if "CRONOLOGIA DEL EVENTO" in df_core_filtered.columns else df_core_filtered.columns[15]

                df_valid_crono = df_core_filtered.dropna(subset=[col_crono]).copy()
                df_valid_crono["Crono_Str"] = df_valid_crono[col_crono].astype(str)

                dwdm_df = df_valid_crono[df_valid_crono["Crono_Str"].str.contains("DWDM", case=False, na=False)]
                metro_df = df_valid_crono[df_valid_crono["Crono_Str"].str.contains("METRO", case=False, na=False)]
                isp_df = df_valid_crono[df_valid_crono["Crono_Str"].str.contains("ISP", case=False, na=False)]
                icx_df = df_valid_crono[df_valid_crono["Crono_Str"].str.contains("INTERCONEXI", case=False, na=False)]

                txt_dwdm = "\n".join([f"-{row['Fecha_Texto']} {row['Crono_Str'].strip()}" for _, row in dwdm_df.iterrows()]) if not dwdm_df.empty else "-NINGUNO"
                txt_metro = "\n".join([f"-{row['Fecha_Texto']} {row['Crono_Str'].strip()}" for _, row in metro_df.iterrows()]) if not metro_df.empty else "-NINGUNO"
                txt_isp = "\n".join([f"-{row['Fecha_Texto']} {row['Crono_Str'].strip()}" for _, row in isp_df.iterrows()]) if not isp_df.empty else "-Ninguno"
                txt_icx = "\n".join([f"-{row['Fecha_Texto']} {row['Crono_Str'].strip()}" for _, row in icx_df.iterrows()]) if not icx_df.empty else "- Ninguno"

                msg_core = (
                    f"Buenos dias Juanjo,\n\n"
                    f"*Eventos de consideración RED CORE:*\n"
                    f"-SIN EVENTOS\n\n"
                    f"*Eventos DWDM:*\n"
                    f"{txt_dwdm}\n\n"
                    f"*Eventos METRO:*\n"
                    f"{txt_metro}\n\n"
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
