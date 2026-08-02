import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión de Eventos Pendientes", page_icon="🚨", layout="wide")

st.title("🚨 Gestión y Reporte de Eventos Pendientes")

uploaded_file = st.sidebar.file_uploader("Cargar archivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df_raw = pd.read_excel(uploaded_file)
        
        # Limpiar espacios en los nombres de columnas
        df_raw.columns = [str(col).strip() for col in df_raw.columns]
        
        # Identificar la columna AG (posición 32 de base 0, la 33ª columna)
        col_ag_nombre = None
        if len(df_raw.columns) >= 33:
            col_ag_nombre = df_raw.columns[32]  # Toma el nombre exacto de la columna AG
        
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
                # Filtrar solo aquellos cuya columna AG sea igual a "PENDIENTE"
                df = df[df[col_ag_nombre].astype(str).str.strip().str.upper() == "PENDIENTE"]
            # --------------------------------------------------

            df = df[cols_existentes].copy()

            # Procesamiento de Fechas
            df["Fecha_DT"] = pd.to_datetime(df["FECHA INICIO"], dayfirst=True, errors="coerce")
            df = df.dropna(subset=["Fecha_DT"])

            df["Año"] = df["Fecha_DT"].dt.year
            df["Mes_Num"] = df["Fecha_DT"].dt.month

            meses_es = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            df["Mes"] = df["Mes_Num"].map(meses_es)
            df["Semana"] = df["Fecha_DT"].dt.isocalendar().week

            # Barra Lateral - Filtros
            st.sidebar.header("🔍 Filtros")
            
            # Filtro por Rango de Fechas
            if not df.empty:
                min_date = df["Fecha_DT"].min().date()
                max_date = df["Fecha_DT"].max().date()
                
                date_range = st.sidebar.date_input(
                    "Rango de Fechas",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    format="DD/MM/YYYY"
                )
            else:
                date_range = None

            anios_opt = sorted(df["Año"].unique(), reverse=True)
            selected_anios = st.sidebar.multiselect("Año", options=anios_opt, default=anios_opt)

            meses_opt = df[df["Año"].isin(selected_anios)].sort_values("Mes_Num")["Mes"].unique().tolist()
            selected_meses = st.sidebar.multiselect("Mes", options=meses_opt, default=meses_opt)

            semanas_opt = sorted(df[(df["Año"].isin(selected_anios)) & (df["Mes"].isin(selected_meses))]["Semana"].unique())
            selected_semanas = st.sidebar.multiselect("Semana del Año", options=semanas_opt, default=semanas_opt)

            ciudades_opt = sorted(df["CIUDAD"].dropna().astype(str).unique())
            selected_ciudades = st.sidebar.multiselect("Ciudad", options=ciudades_opt, default=ciudades_opt)

            # Aplicar Filtros generales
            mask = (
                (df["Año"].isin(selected_anios)) &
                (df["Mes"].isin(selected_meses)) &
                (df["Semana"].isin(selected_semanas)) &
                (df["CIUDAD"].isin(selected_ciudades))
            )

            # Validar rango de fechas
            if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                mask = mask & (df["Fecha_DT"].dt.date >= start_date) & (df["Fecha_DT"].dt.date <= end_date)

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
            
            df_display = df_filtered[cols_existentes].copy()
            df_display["FECHA INICIO"] = df_filtered["Fecha_DT"].dt.strftime("%d-%m-%Y")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Módulo WhatsApp
            st.markdown("---")
            st.subheader("📲 Reporte para WhatsApp")

            if not df_filtered.empty:
                lineas_reporte = []
                lineas_reporte.append("🚨 *REPORTE DE EVENTOS PENDIENTES* 🚨\n")
                lineas_reporte.append(f"📊 *Total Pendientes:* {len(df_filtered)}")
                
                if "IMPACTO" in df_filtered.columns:
                    desglose_txt = ", ".join([f"{k}: {v}" for k, v in desglose.items()])
                    lineas_reporte.append(f"📌 *Impacto:* {desglose_txt}")
                
                lineas_reporte.append("-----------------------------------")

                for ciudad, grupo in df_filtered.groupby("CIUDAD"):
                    lineas_reporte.append(f"\n📍 *CIUDAD: {str(ciudad).upper()}* ({len(grupo)})")
                    
                    for idx, row in grupo.iterrows():
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
                st.text_area("Copia el siguiente texto para enviarlo por WhatsApp:", texto_whatsapp, height=300)
            else:
                st.warning("No hay eventos que coincidan con los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👈 Por favor, carga el archivo Excel en la barra lateral.")
