import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Painel de Vendas", layout="wide")

# Carregar dados com tratamento
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados_vendas.csv", parse_dates=['data'], dayfirst=True)
    df['regiao'] = df['regiao'].str.strip()  # Remove espaços extras
    df['data'] = pd.to_datetime(df['data'])  # Garante o tipo datetime
    return df

df = carregar_dados()

# Obter regiões únicas (tratamento especial para Centro-Oeste)
regioes_unicas = df['regiao'].unique().tolist()
if "Centro-Oeste" not in regioes_unicas:
    regioes_unicas.append("Centro-Oeste")
TODAS_REGIOES = sorted(list(set(regioes_unicas)))  # Remove duplicatas e ordena

# Sidebar com filtros
st.sidebar.header("Filtros")

# Filtro de data
data_min = df['data'].min().date()
data_max = df['data'].max().date()
data_inicio = st.sidebar.date_input("Data inicial", data_min)
data_fim = st.sidebar.date_input("Data final", data_max)

# Filtro de categoria
categorias = st.sidebar.multiselect(
    "Categorias",
    options=sorted(df['categoria'].unique()),
    default=sorted(df['categoria'].unique())
)

# Filtro de região (sem duplicatas)
regioes = st.sidebar.multiselect(
    "Regiões",
    options=TODAS_REGIOES,
    default=TODAS_REGIOES
)

# Aplicar filtros
try:
    df_filtrado = df[
        (df['data'].dt.date >= data_inicio) & 
        (df['data'].dt.date <= data_fim) & 
        (df['categoria'].isin(categorias)) & 
        (df['regiao'].isin([r.strip() for r in regioes]))
    ]
except Exception as e:
    st.error(f"Erro ao filtrar dados: {e}")
    df_filtrado = df.copy()

# Abas principais
tab1, tab2, tab3, tab4 = st.tabs(["📈 Visão Geral", "🧑‍💼 Vendedores", "📦 Produtos", "👥 Clientes"])

with tab1:
    st.header("Visão Geral das Vendas")

    if not df_filtrado.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Vendido", f"R$ {df_filtrado['valor'].sum():,.2f}")
        col2.metric("Número de Vendas", df_filtrado.shape[0])
        col3.metric("Média por Venda", f"R$ {df_filtrado['valor'].mean():,.2f}")

        fig1 = px.line(
            df_filtrado.groupby('data')['valor'].sum().reset_index(),
            x='data',
            y='valor',
            title='Vendas por Dia'
        )
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.bar(
            df_filtrado.groupby('categoria')['valor'].sum().reset_index(),
            x='categoria',
            y='valor',
            title='Vendas por Categoria'
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Mapa por região
        coordenadas = {
            "Norte": {"lat": -3.1, "lon": -60.0},
            "Nordeste": {"lat": -7.2, "lon": -43.0},
            "Centro-Oeste": {"lat": -15.6, "lon": -55.0},
            "Sudeste": {"lat": -20.1, "lon": -47.0},
            "Sul": {"lat": -28.0, "lon": -51.0},
        }

        df_mapa = df_filtrado.groupby("regiao")["valor"].sum().reset_index()
        df_mapa = df_mapa[df_mapa['regiao'].isin(regioes)]
        
        if not df_mapa.empty:
            df_mapa["lat"] = df_mapa["regiao"].map(lambda x: coordenadas.get(x.strip())["lat"])
            df_mapa["lon"] = df_mapa["regiao"].map(lambda x: coordenadas.get(x.strip())["lon"])

            fig_mapa = px.scatter_geo(
                df_mapa,
                lat="lat",
                lon="lon",
                scope="south america",
                size="valor",
                color="regiao",
                hover_name="regiao",
                size_max=40,
                title="Total Vendido por Região (Mapa)"
            )
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.warning("Nenhuma região selecionada possui dados para exibir no mapa")
    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados")

with tab2:
    st.header("Desempenho por Vendedor")
    
    if not df_filtrado.empty:
        fig3 = px.bar(
            df_filtrado.groupby('vendedor')['valor'].sum().reset_index().sort_values('valor', ascending=False),
            x='vendedor',
            y='valor',
            title='Total de Vendas por Vendedor'
        )
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = px.pie(
            df_filtrado.groupby('vendedor')['valor'].sum().reset_index(),
            names='vendedor',
            values='valor',
            title='Participação nas Vendas'
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados")

with tab3:
    st.header("Análise de Produtos")
    
    if not df_filtrado.empty:
        fig5 = px.bar(
            df_filtrado.groupby('produto')['quantidade'].sum().reset_index().sort_values('quantidade', ascending=False).head(10),
            x='produto',
            y='quantidade',
            title='Produtos Mais Vendidos (Quantidade)'
        )
        st.plotly_chart(fig5, use_container_width=True)

        fig6 = px.scatter(
            df_filtrado.groupby('produto').agg({'quantidade': 'sum', 'valor': 'sum'}).reset_index(),
            x='quantidade',
            y='valor',
            size='valor',
            color='produto',
            title='Relação Quantidade vs Valor'
        )
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados")

with tab4:
    st.header("Análise de Clientes")
    
    if not df_filtrado.empty:
        clientes_valor = df_filtrado.groupby('cliente')['valor'].sum().reset_index()
        fig7 = px.bar(
            clientes_valor.nlargest(10, 'valor'),
            x='cliente',
            y='valor',
            title='Top 10 Clientes (Valor Total)',
            color='valor'
        )
        st.plotly_chart(fig7, use_container_width=True)
        
        clientes_freq = df_filtrado['cliente'].value_counts().reset_index()
        clientes_freq.columns = ['cliente', 'qtd_compras']
        fig8 = px.bar(
            clientes_freq.head(10),
            x='cliente',
            y='qtd_compras',
            title='Clientes Mais Frequentes',
            color='qtd_compras'
        )
        st.plotly_chart(fig8, use_container_width=True)
        
        st.subheader("Detalhes por Cliente")
        resumo_clientes = df_filtrado.groupby('cliente').agg({
            'valor': 'sum',
            'data': 'count',
            'regiao': lambda x: x.mode()[0],
            'produto': lambda x: ", ".join(x.unique()[:3]) + ("..." if len(x.unique()) > 3 else "")
        }).rename(columns={
            'valor': 'Valor Total',
            'data': 'Qtd Compras'
        }).sort_values('Valor Total', ascending=False)
        
        st.dataframe(
            resumo_clientes,
            use_container_width=True,
            height=500
        )
    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados")

# Rodapé
st.markdown("---")
st.markdown("**Projeto 01 - Visualização de Dados P3**")