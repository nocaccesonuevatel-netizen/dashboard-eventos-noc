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
    st.title("🚨 Gestión y Reporte de Eventos Pendientes (Año 2026)")

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
            
            # Columnas requeridas
            columnas_deseadas = [
                "FECHA INICIO", "HORA INICIO", "IMPACTO", "ZONA AFECTADA", 
                "CIUDAD", "CELL ID", "TECNOLOGIAS AFECTADAS", 
                "SERVICIOS AFECTADOS", "CAUSA PRELIMINAR"
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

                df = df[cols_existentes].copy()

                # Procesamiento y Limpieza de Fechas
                df["Fecha_DT"] = pd.to_datetime(df["FECHA INICIO"], dayfirst=True, errors="coerce")
                df = df.dropna(subset=["Fecha_DT"])

                # --- FILTRAR ÚNICAMENTE INFORMACIÓN DEL 2026 ---
                df = df[df["Fecha_DT"].dt.year == 2026]

                if df.empty:
                    st.warning("⚠️ No se encontraron eventos pendientes correspondientes al año 2026.")
                else:
                    # Barra Lateral - Filtro por Fecha
                    st.sidebar.header("🔍 Filtros (Pendientes)")
                    
                    min_f = df["Fecha_DT"].min().date()
                    max_f = df["Fecha_DT"].max().date()

                    selected_date = st.sidebar.date_input(
                        "Mostrar eventos desde esta fecha en adelante:",
                        value=min_f,
                        min_value=datetime.date(2026, 1, 1),
                        max_value=datetime.date(2026, 12, 31),
                        format="DD/MM/YYYY",
                        key="date_pendientes"
                    )

                    ciudades_opt = sorted(df["CIUDAD"].dropna().astype(str).unique())
                    selected_ciudades = st.sidebar.multiselect("Ciudad", options=ciudades_opt, default=ciudades_opt, key="ciudades_pend")

                    # Aplicar Máscara de Filtro (Fecha en adelante + Ciudades)
                    mask = (df["Fecha_DT"].dt.date >= selected_date) & (df["CIUDAD"].isin(selected_ciudades))
                    df_filtered = df[mask].copy()

                    # Visualización KPIs y Tabla
                    st.subheader("📊 Resumen General")
                    col1, col2 = st.columns(2)
                    
                    total_pendientes_filtrados = len(df_filtered)
                    col1.metric("Total Eventos Pendientes", total_pendientes_filtrados)

                    desglose_wa = ""
                    if not df_filtered.empty and "IMPACTO" in df_filtered.columns:
                        desglose_dic = df_filtered["IMPACTO"].value_counts().to_dict()
                        texto_impacto = " | ".join([f"**{k}:** {v}" for k, v in desglose_dic.items()])
                        desglose_wa = ", ".join([f"{k}: {v}" for k, v in desglose_dic.items()])
                        col2.markdown(f"**Desglose por Impacto:**\n\n{texto_impacto}")

                    st.markdown("---")
                    st.subheader("📋 Detalle de Eventos Filtrados")
                    
                    df_display = df_filtered[cols_existentes].copy()
                    df_display["FECHA INICIO"] = df_filtered["Fecha_DT"].dt.strftime("%d-%m-%Y")
                    st.dataframe(df_display, use_container_width=True, hide_index=True)

                    # Módulo WhatsApp Sincronizado
                    st.markdown("---")
                    st.subheader("📲 Reporte para WhatsApp")

                    if not df_filtered.empty:
                        lineas_reporte = []
                        lineas_reporte.append("🚨 *REPORTE DE EVENTOS PENDIENTES (2026)* 🚨\n")
                        lineas_reporte.append(f"📊 *Total Pendientes:* {total_pendientes_filtrados}")
                        
                        if desglose_wa:
                            lineas_reporte.append(f"📌 *Impacto:* {desglose_wa}")
                        
                        lineas_reporte.append("-----------------------------------")

                        for ciudad, grupo in df_filtered.groupby("CIUDAD"):
                            lineas_reporte.append(f"\n📍 *CIUDAD: {str(ciudad).upper()}* ({len(grupo)})")
                            
                            for _, row in grupo.iterrows():
                                fecha_str = row["Fecha_DT"].strftime("%d/%m/%Y")
                                hora_str = str(row.get("HORA INICIO", "N/I"))[:5]
                                zona = row.get("ZONA AFECTADA", "N/A")
                                impacto = row.get("IMPACTO", "N/A")
                                causa = row.get("CAUSA PRELIMINAR", "N/A")
                                cell_id = row.get("CELL ID", "N/A")
                                
                                lineas_reporte.append(
                                    f"• *{zona}*"
                                    f"\n  └ 🗓️ {fecha_str} {hora_str} | ⚠️ {impacto}"
                                    f"\n  └ 📡 *CELL ID:* {cell_id}"
                                    f"\n  └ 🔍 *Causa:* {causa}"
                                )

                        texto_whatsapp = "\n".join(lineas_reporte)
                        
                        # Usar clave dinámica basada en la fecha para forzar la actualización inmediata en pantalla
                        st.text_area(
                            "Copia el siguiente texto para enviarlo por WhatsApp:", 
                            texto_whatsapp, 
                            height=300, 
                            key=f"txt_wa_pend_{selected_date}_{len(df_filtered)}"
                        )
                    else:
                        st.warning("No hay eventos que coincidan con los filtros seleccionados.")

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    else:
        st.info("👈 Por favor, carga el archivo Excel en la barra lateral.")

# ==============================================================================
# MÓDULO 2: REPORTE MATUTINO (RED ACCESO Y RED CORE)
# ==============================================================================
with tab_matutino:
    st.title("🌅 Reporte Matutino Diario")

    # Selector de Turno/Área
    area_turno = st.radio("Selecciona tu Área de Turno:", ["RED ACCESO", "RED CORE"], horizontal=True)
    st.markdown("---")

    uploaded_matutino = st.file_uploader(f"Cargar Excel ({area_turno})", type=["xlsx", "xls"], key="uploader_matutino")

    # --------------------------------------------------------------------------
    # ÁREA: RED ACCESO
    # --------------------------------------------------------------------------
    else:
        st.subheader("🧠 Reporte Diario - RED CORE")

        if uploaded_matutino is not None:
            try:
                df_core_raw = pd.read_excel(uploaded_matutino)
                df_core_raw.columns = [str(c).strip() for c in df_core_raw.columns]

                # Tomar la Columna C1 (Posición índice 2) para la Fecha de Inicio
                col_fecha_c1 = df_core_raw.columns[2] if len(df_core_raw.columns) >= 3 else df_core_raw.columns[0]
                df_core_raw["Fecha_DT"] = pd.to_datetime(df_core_raw[col_fecha_c1], dayfirst=True, errors="coerce")
                
                # --- FILTRO EXCLUSIVO DEL AÑO 2026 EN ADELANTE ---
                df_core_raw = df_core_raw[df_core_raw["Fecha_DT"].dt.year >= 2026]

                if df_core_raw.empty:
                    st.warning("⚠️ No se encontraron registros en RED CORE del año 2026 en adelante.")
                else:
                    # Crear texto legible solo de fecha de inicio [DD/MM/YYYY]
                    df_core_raw["Fecha_Texto"] = df_core_raw["Fecha_DT"].dt.strftime("[%d/%m/%Y]")
                    df_core_raw["Fecha_Texto"] = df_core_raw["Fecha_Texto"].fillna("")

                    # Selector de fecha tipo calendario
                    col_f1, col_f2 = st.columns([2, 1])
                    filtrar_por_fecha = col_f2.checkbox("Filtrar por fecha", value=True)

                    if filtrar_por_fecha and df_core_raw["Fecha_DT"].notna().any():
                        # Obtener fechas mínimas/máximas asegurando que no sean menores al 2026
                        min_fecha_data = df_core_raw["Fecha_DT"].min().date()
                        max_fecha_data = df_core_raw["Fecha_DT"].max().date()

                        fecha_inicial_picker = max(min_fecha_data, datetime.date(2026, 1, 1))

                        selected_date_core = col_f1.date_input(
                            "📅 Mostrar eventos desde la Fecha (Columna C1):",
                            value=fecha_inicial_picker,
                            min_value=datetime.date(2026, 1, 1),
                            max_value=datetime.date(2026, 12, 31),
                            format="DD/MM/YYYY",
                            key="date_core_cal"
                        )
                        
                        # Filtra desde la fecha seleccionada en adelante
                        df_core_filtered = df_core_raw[df_core_raw["Fecha_DT"].dt.date >= selected_date_core]
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

                    # Identificar la columna P1 (índice 15) para la Cronología del Evento
                    col_crono = "CRONOLOGIA DEL EVENTO" if "CRONOLOGIA DEL EVENTO" in df_core_filtered.columns else df_core_filtered.columns[15]

                    # Búsqueda flexible de palabras clave incluyendo únicamente la fecha de inicio
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

                    # Generar Mensaje WhatsApp con negritas (*texto*)
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
                    st.info("💡 **Tip:** Haz clic en el icono 📋 arriba a la derecha del recuadro para copiar.")
                    st.code(msg_core, language=None)

            except Exception as e:
                st.error(f"Error al procesar el archivo de CORE: {e}")
        else:
            st.info("👈 Por favor, carga el archivo Excel para generar automáticamente el reporte de RED CORE.")
        else:
            st.info("👈 Por favor, carga el archivo Excel para generar automáticamente el reporte de RED CORE.")
