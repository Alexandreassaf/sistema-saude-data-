"""
╔══════════════════════════════════════════════════════════════════╗
║        SISTEMA SAÚDE INTEGRATIVA - MEDICINA ORTOMOLECULAR        ║
║                    Versão 1.0 | 2025                            ║
║           Desenvolvido para uso profissional (Naturopatia)       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path

# ══════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ══════════════════════════════════════════════════
st.set_page_config(
    page_title="Sistema Saúde Integrativa",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════
# CSS CUSTOMIZADO
# ══════════════════════════════════════════════════
st.markdown("""
<style>
    /* Fonte e cores globais */
    .main { background-color: #f8f9fa; }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #1a6b3a 0%, #2d9e5f 100%);
        padding: 20px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        text-align: center;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p { margin: 5px 0 0 0; opacity: 0.9; }

    /* Cards de suplementos */
    .supp-card-essencial {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .supp-card-padrao {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .supp-card-opcional {
        background: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }

    /* Alertas */
    .alert-critico {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #721c24;
    }
    .alert-moderado {
        background: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #856404;
    }

    /* Métricas customizadas */
    .metric-box {
        background: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #1a6b3a; }
    .metric-label { font-size: 0.8rem; color: #6c757d; }

    /* Protocolo diário */
    .timing-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        border-top: 3px solid #2d9e5f;
    }

    /* Badge de rating */
    .rating-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    
    /* Footer */
    .footer-note {
        background: #f1f3f4;
        border-radius: 8px;
        padding: 12px;
        font-size: 0.82rem;
        color: #6c757d;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# FUNÇÕES DE DADOS
# ══════════════════════════════════════════════════

@st.cache_resource
def carregar_doencas():
    """Carrega todos os JSONs de doenças da pasta data/"""
    data_path = Path(__file__).parent / "data"
    doencas = {}

    if not data_path.exists():
        return {}

    for json_file in sorted(data_path.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                doenca_id = dados['meta']['id']
                doencas[doenca_id] = dados
        except Exception as e:
            st.error(f"Erro ao carregar {json_file.name}: {e}")

    return doencas


def get_stars(rating):
    """Converte rating numérico em estrelas"""
    return "⭐" * rating + "☆" * (5 - rating)


def get_stars_emoji(rating):
    """Stars compactas"""
    return "★" * rating + "☆" * (5 - rating)


# ══════════════════════════════════════════════════
# MOTOR DE RECOMENDAÇÃO
# ══════════════════════════════════════════════════

def identificar_cenario(doenca_dados, hba1c, homa_ir, complicacoes):
    """Identifica o melhor cenário clínico para o paciente"""
    cenarios = doenca_dados.get('cenarios_clinicos', [])

    # Prioridade: complicações específicas
    for comp in complicacoes:
        for cenario in cenarios:
            if cenario.get('complicacao', '').lower() == comp.lower():
                return cenario

    # Cenário por HbA1c
    melhor = None
    for cenario in cenarios:
        hba1c_min = cenario.get('hba1c_min', 0)
        hba1c_max = cenario.get('hba1c_max', 99)
        if hba1c_min <= hba1c <= hba1c_max:
            melhor = cenario
            break

    return melhor or (cenarios[0] if cenarios else None)


def verificar_contraindicacoes(suplemento, medicamentos, condicoes):
    """Verifica se suplemento é seguro para o paciente"""
    alertas = []
    contraindicado = False

    # Contraindicações absolutas
    for contra in suplemento.get('contraindicacoes_absolutas', []):
        for cond in condicoes + medicamentos:
            if contra.lower() in cond.lower() or cond.lower() in contra.lower():
                contraindicado = True
                alertas.append({
                    'tipo': 'critico',
                    'mensagem': f"CONTRAINDICADO: {contra}"
                })

    # Interações medicamentosas
    for interacao in suplemento.get('interacoes', []):
        farmaco = interacao.get('farmaco', '')
        for med in medicamentos:
            if farmaco.lower() in med.lower() or med.lower() in farmaco.lower():
                severidade = interacao.get('severidade', 'baixa')
                if severidade == 'alta':
                    contraindicado = True
                    alertas.append({
                        'tipo': 'critico',
                        'mensagem': f"Interação GRAVE com {med}: {interacao.get('efeito', '')}. {interacao.get('manejo', '')}"
                    })
                elif severidade == 'moderada':
                    alertas.append({
                        'tipo': 'moderado',
                        'mensagem': f"Interação com {med}: {interacao.get('efeito', '')}. {interacao.get('manejo', '')}"
                    })

    return contraindicado, alertas


def calcular_score(suplemento, cenario, perfil):
    """Calcula score de prioridade do suplemento"""
    nnt = suplemento.get('nnt', 10)
    rating = suplemento.get('rating', 3)
    custo = suplemento.get('custo_medio', 200)
    supp_id = suplemento['id']

    # Bonus por estar no cenário
    bonus_cenario = 0
    if supp_id in cenario.get('suplementos_essenciais', []):
        bonus_cenario = 50
    elif supp_id in cenario.get('suplementos_padrão', []):
        bonus_cenario = 30
    elif supp_id in cenario.get('suplementos_premium', []):
        bonus_cenario = 15

    # Bonus por mecanismo relevante
    bonus_mecanismo = 0
    mecanismos_criticos = perfil.get('mecanismos_criticos', [])
    for mec in suplemento.get('mecanismos_alvo', []):
        if mec in mecanismos_criticos:
            bonus_mecanismo += 10

    # Cálculo score
    score_nnt = max(0, (10 - nnt)) * 10
    score_rating = rating * 12
    score_custo = max(0, (350 - custo) / 8)

    return score_nnt + score_rating + score_custo + bonus_cenario + bonus_mecanismo


def gerar_recomendacoes(doenca_dados, cenario, orcamento, medicamentos, condicoes, perfil_paciente):
    """Gera lista de recomendações personalizadas por orçamento"""
    suplementos = doenca_dados.get('suplementos', [])

    recomendados = []
    excluidos = []
    todos_alertas = []

    for supp in suplementos:
        # Verificar segurança
        contraindicado, alertas = verificar_contraindicacoes(supp, medicamentos, condicoes)

        if contraindicado:
            excluidos.append({'suplemento': supp, 'motivo': alertas})
            todos_alertas.extend(alertas)
        else:
            todos_alertas.extend(alertas)
            score = calcular_score(supp, cenario, perfil_paciente)
            supp_copy = supp.copy()
            supp_copy['_score'] = score
            supp_copy['_alertas'] = alertas
            recomendados.append(supp_copy)

    # Ordenar por score
    recomendados.sort(key=lambda x: x['_score'], reverse=True)

    # Selecionar por orçamento
    selecionados = []
    custo_total = 0

    # 1. Primeiro: essenciais do cenário
    essenciais = cenario.get('suplementos_essenciais', []) if cenario else []
    for supp in recomendados:
        if supp['id'] in essenciais:
            custo = supp.get('custo_medio', 100)
            if custo_total + custo <= orcamento:
                supp['_prioridade'] = 'Essencial'
                supp['_prioridade_cor'] = 'essencial'
                selecionados.append(supp)
                custo_total += custo

    # 2. Depois: padrão e premium
    padrao = cenario.get('suplementos_padrão', []) if cenario else []
    premium = cenario.get('suplementos_premium', []) if cenario else []

    for supp in recomendados:
        if supp not in selecionados:
            custo = supp.get('custo_medio', 100)
            if custo_total + custo <= orcamento:
                if supp['id'] in padrao:
                    supp['_prioridade'] = 'Padrão'
                    supp['_prioridade_cor'] = 'padrao'
                elif supp['id'] in premium:
                    supp['_prioridade'] = 'Premium'
                    supp['_prioridade_cor'] = 'opcional'
                else:
                    supp['_prioridade'] = 'Opcional'
                    supp['_prioridade_cor'] = 'opcional'
                selecionados.append(supp)
                custo_total += custo

    return selecionados, excluidos, todos_alertas, custo_total


def gerar_protocolo_diario(selecionados):
    """Organiza suplementos por horário"""
    horarios = {
        'Jejum (ao acordar)': [],
        'Café da manhã': [],
        '15-30 min antes almoço': [],
        'Almoço': [],
        'Lanche': [],
        '15-30 min antes jantar': [],
        'Jantar': [],
        'Noite (antes de dormir)': []
    }

    mapeamento_timing = {
        'jejum': 'Jejum (ao acordar)',
        'jejum_ou_antes_jantar': 'Jejum (ao acordar)',
        'manha': 'Café da manhã',
        'manha_com_refeicao': 'Café da manhã',
        'com_refeicao_gordurosa': 'Café da manhã',
        'manha_e_noite': 'Café da manhã',
        '15min_antes_refeicao': '15-30 min antes almoço',
        '20-30min_antes_refeicao': '15-30 min antes almoço',
        '30min_antes_refeicao': '15-30 min antes almoço',
        '30-60min_antes_refeicao': '15-30 min antes almoço',
        'com_refeicao': 'Almoço',
        'qualquer_horario': 'Café da manhã',
        'com_ou_sem_refeicao': 'Almoço',
        'com_refeicao_nao_noite': 'Almoço',
        'noite': 'Noite (antes de dormir)',
        '30-60min_antes_dormir': 'Noite (antes de dormir)',
        'jejum_ou_longe_calcio': 'Jejum (ao acordar)',
        'manha_com_refeicao_e_noite': 'Café da manhã',
    }

    for supp in selecionados:
        timing_key = supp.get('timing', 'com_refeicao')
        horario = mapeamento_timing.get(timing_key, 'Almoço')

        # Se divisões = 2+, distribuir
        divisoes = supp.get('divisoes_dia', 1)
        if divisoes >= 2 and timing_key not in ['manha_e_noite', 'manha_com_refeicao_e_noite']:
            # Adicionar em 2 momentos
            horarios[horario].append(supp)
            if 'manha' in timing_key or 'refeicao' in timing_key:
                horarios['Jantar'].append(supp)
        else:
            horarios[horario].append(supp)

    return {k: v for k, v in horarios.items() if v}


# ══════════════════════════════════════════════════
# COMPONENTES DE UI
# ══════════════════════════════════════════════════

def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>🌿 Sistema Saúde Integrativa</h1>
        <p>Medicina Ortomolecular · Naturopatia · Fitoterapia · Nutrição Funcional</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_form(doencas):
    """Formulário do paciente na sidebar"""
    with st.sidebar:
        st.markdown("## 👤 Perfil do Paciente")

        # Seleção da doença
        doenca_opcoes = {v['meta']['nome']: k for k, v in doencas.items()}
        if not doenca_opcoes:
            st.error("Nenhuma doença carregada. Verifique a pasta data/")
            return None

        doenca_nome = st.selectbox(
            "🏥 Doença Principal",
            options=list(doenca_opcoes.keys())
        )
        doenca_id = doenca_opcoes[doenca_nome]
        doenca_dados = doencas[doenca_id]

        st.divider()

        # Dados clínicos
        st.markdown("### 📊 Dados Clínicos")

        col1, col2 = st.columns(2)
        with col1:
            idade = st.number_input("Idade", 18, 100, 50)
        with col2:
            sexo = st.selectbox("Sexo", ["Masculino", "Feminino"])

        # Marcadores específicos da doença
        meta_id = doenca_dados['meta']['id']

        if meta_id == "DM2":
            hba1c = st.slider("HbA1c (%)", 4.0, 14.0, 7.5, 0.1)
            homa_ir = st.slider("HOMA-IR", 1.0, 15.0, 5.0, 0.5)
            col1, col2 = st.columns(2)
            with col1:
                glicemia = st.number_input("Glicemia jejum (mg/dL)", 60, 500, 140)
            with col2:
                tgp = st.number_input("TGP (U/L)", 10, 500, 45)
        else:
            hba1c = 7.0
            homa_ir = 3.0
            glicemia = 126
            tgp = 35

        st.divider()

        # Comorbidades / Complicações
        st.markdown("### 🔍 Complicações Presentes")
        complicacoes = []
        if meta_id == "DM2":
            if st.checkbox("Neuropatia Periférica"):
                complicacoes.append("neuropatia")
            if st.checkbox("NAFLD / TGP elevado"):
                complicacoes.append("NAFLD")
            if st.checkbox("Hipertensão Arterial"):
                complicacoes.append("HAS")
            if st.checkbox("DRC / Albuminúria"):
                complicacoes.append("DRC")
            if st.checkbox("SOP (mulheres)"):
                complicacoes.append("SOP")

        st.divider()

        # Medicamentos em uso
        st.markdown("### 💊 Medicamentos em Uso")
        medicamentos = []

        if meta_id == "DM2":
            if st.checkbox("Metformina"):
                medicamentos.append("metformina")
            if st.checkbox("Insulina"):
                medicamentos.append("insulina")
            if st.checkbox("Sulfonilureia (Glibenclamida, Gliclazida)"):
                medicamentos.append("sulfonilureias")
            if st.checkbox("Estatina (Sinvastatina, Atorvastatina)"):
                medicamentos.append("estatinas")
            if st.checkbox("Varfarina / Anticoagulante"):
                medicamentos.append("varfarina")
            if st.checkbox("Imunossupressor (Ciclosporina, Tacrolimus)"):
                medicamentos.append("ciclosporina")
                medicamentos.append("tacrolimus")

        # Condições especiais
        condicoes = []
        st.markdown("### ⚠️ Condições Especiais")
        if st.checkbox("Gestação"):
            condicoes.append("gestacao")
        if st.checkbox("Lactação"):
            condicoes.append("lactacao")
        if st.checkbox("IRC grave (eGFR <30)"):
            condicoes.append("IRC_grave")
            condicoes.append("IRC_grave_eGFR<30")

        st.divider()

        # Orçamento
        st.markdown("### 💰 Orçamento Mensal")
        orcamento = st.slider(
            "Valor disponível (R$/mês)",
            min_value=100,
            max_value=1500,
            value=400,
            step=50
        )

        # Indicador de nível
        if orcamento < 300:
            st.info("💚 Protocolo Essencial")
        elif orcamento < 600:
            st.warning("💛 Protocolo Padrão")
        else:
            st.success("💙 Protocolo Premium")

        st.divider()

        # Botão de gerar
        gerar = st.button(
            "🔬 GERAR PROTOCOLO",
            use_container_width=True,
            type="primary"
        )

        return {
            'doenca_id': doenca_id,
            'doenca_dados': doenca_dados,
            'idade': idade,
            'sexo': sexo,
            'hba1c': hba1c,
            'homa_ir': homa_ir,
            'glicemia': glicemia,
            'tgp': tgp,
            'complicacoes': complicacoes,
            'medicamentos': medicamentos,
            'condicoes': condicoes,
            'orcamento': orcamento,
            'gerar': gerar
        }


def render_resumo_paciente(perfil):
    """Card de resumo do paciente"""
    doenca = perfil['doenca_dados']['meta']['nome']
    meta_id = perfil['doenca_dados']['meta']['id']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Doença</div>
            <div style="font-size:1rem; font-weight:bold; color:#1a6b3a">{doenca}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        if meta_id == "DM2":
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">HbA1c</div>
                <div class="metric-value">{perfil['hba1c']}%</div>
            </div>""", unsafe_allow_html=True)

    with col3:
        if meta_id == "DM2":
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">HOMA-IR</div>
                <div class="metric-value">{perfil['homa_ir']}</div>
            </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Orçamento</div>
            <div class="metric-value">R${perfil['orcamento']}</div>
        </div>""", unsafe_allow_html=True)


def render_alertas(alertas, excluidos):
    """Exibe alertas de segurança"""
    if not alertas and not excluidos:
        return

    with st.expander("⚠️ ALERTAS DE SEGURANÇA", expanded=True):
        for alerta in alertas:
            if alerta['tipo'] == 'critico':
                st.markdown(f"""
                <div class="alert-critico">
                    🚨 <strong>ATENÇÃO:</strong> {alerta['mensagem']}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-moderado">
                    ⚠️ <strong>Monitorar:</strong> {alerta['mensagem']}
                </div>""", unsafe_allow_html=True)

        if excluidos:
            st.markdown("**Suplementos EXCLUÍDOS por contraindicação:**")
            for exc in excluidos:
                motivos = [m['mensagem'] for m in exc['motivo']]
                st.markdown(f"- ~~{exc['suplemento']['nome']}~~: {', '.join(motivos)}")


def render_lista_suplementos(selecionados, custo_total):
    """Exibe lista de suplementos recomendados"""
    st.markdown(f"### 💊 Protocolo Recomendado — Total: R$ {custo_total:.0f}/mês")

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_prioridade = st.multiselect(
            "Filtrar por prioridade",
            options=["Essencial", "Padrão", "Premium", "Opcional"],
            default=["Essencial", "Padrão", "Premium"]
        )
    with col2:
        filtro_categoria = st.multiselect(
            "Filtrar por categoria",
            options=list(set(s.get('categoria', '') for s in selecionados)),
            default=[]
        )

    # Aplicar filtros
    filtrados = selecionados.copy()
    if filtro_prioridade:
        filtrados = [s for s in filtrados if s.get('_prioridade', '') in filtro_prioridade]
    if filtro_categoria:
        filtrados = [s for s in filtrados if s.get('categoria', '') in filtro_categoria]

    # Tabela resumo
    if filtrados:
        dados_tabela = []
        for supp in filtrados:
            dados_tabela.append({
                'Prioridade': supp.get('_prioridade', ''),
                'Suplemento': supp['nome'],
                'Rating': get_stars(supp.get('rating', 3)),
                'NNT': supp.get('nnt', '-'),
                'Dose': supp.get('dose_padrao_mg', supp.get('dose_mi_g', '')),
                'Unidade': supp.get('dose_unidade', 'mg/dia'),
                'Divisões/dia': supp.get('divisoes_dia', 1),
                'Custo R$/mês': f"R$ {supp.get('custo_medio', 0):.0f}",
                'Grade': supp.get('evidencia_grade', '').replace('_', ' ').title()
            })

        df = pd.DataFrame(dados_tabela)

        # Colorir por prioridade
        def colorir_linha(row):
            if row['Prioridade'] == 'Essencial':
                return ['background-color: #d4edda'] * len(row)
            elif row['Prioridade'] == 'Padrão':
                return ['background-color: #fff3cd'] * len(row)
            elif row['Prioridade'] == 'Premium':
                return ['background-color: #d1ecf1'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df.style.apply(colorir_linha, axis=1),
            use_container_width=True,
            height=min(400, 40 + len(filtrados) * 38)
        )

    # Cards detalhados
    st.markdown("---")
    st.markdown("### 📋 Detalhes por Suplemento")

    for supp in filtrados:
        prioridade = supp.get('_prioridade', 'Opcional')
        cor = supp.get('_prioridade_cor', 'opcional')

        with st.expander(
            f"{get_stars_emoji(supp.get('rating', 3))} **{supp['nome']}** "
            f"— {prioridade} | NNT={supp.get('nnt', '?')} | "
            f"R$ {supp.get('custo_medio', 0):.0f}/mês"
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Categoria:** {supp.get('categoria', '').replace('_', ' ').title()}")
                st.markdown(f"**Forma preferida:** {supp.get('forma_preferida', '-')}")
                st.markdown(f"**Dose padrão:** {supp.get('dose_unidade', '-')}")
                st.markdown(f"**Timing:** {supp.get('timing', '-').replace('_', ' ')}")
                st.markdown(f"**Evidência:** {supp.get('evidencia_grade', '-').replace('_', ' ').title()}")
                st.markdown(f"**RCTs:** {supp.get('num_rcts', '-')} | **Participantes:** {supp.get('num_participantes', '-')}")

                if supp.get('meta_analise_principal'):
                    st.markdown(f"**Meta-análise:** {supp['meta_analise_principal']}")

            with col2:
                st.markdown(f"**Rating:** {get_stars(supp.get('rating', 3))}")
                st.markdown(f"**NNT:** {supp.get('nnt', '-')}")
                st.markdown(f"**Custo mín:** R$ {supp.get('custo_min', 0):.0f}")
                st.markdown(f"**Custo máx:** R$ {supp.get('custo_max', 0):.0f}")
                if supp.get('marcas_validadas'):
                    marcas = supp['marcas_validadas'][:3]
                    st.markdown(f"**Marcas:** {', '.join(marcas)}")

            # Notas clínicas
            if supp.get('notas_clinicas'):
                st.info(f"📌 {supp['notas_clinicas']}")

            # Alertas do suplemento
            alertas_supp = supp.get('_alertas', [])
            for alerta in alertas_supp:
                if alerta['tipo'] == 'moderado':
                    st.warning(f"⚠️ {alerta['mensagem']}")

            # Sinergias
            sinergias = supp.get('sinergias', [])
            if sinergias:
                st.markdown("**✨ Sinergias validadas:**")
                for sin in sinergias[:3]:
                    st.markdown(
                        f"- + **{sin['suplemento_id'].replace('_', ' ').title()}** "
                        f"({get_stars_emoji(sin['rating'])}): {sin.get('beneficio', '')}"
                    )


def render_protocolo_diario(selecionados):
    """Exibe protocolo organizado por horário"""
    st.markdown("### ⏰ Protocolo Diário — Horários")

    protocolo = gerar_protocolo_diario(selecionados)

    icones_horario = {
        'Jejum (ao acordar)': '🌅',
        'Café da manhã': '☕',
        '15-30 min antes almoço': '🕐',
        'Almoço': '🍽️',
        'Lanche': '🥗',
        '15-30 min antes jantar': '🕕',
        'Jantar': '🌙',
        'Noite (antes de dormir)': '😴'
    }

    for horario, supps in protocolo.items():
        if supps:
            icone = icones_horario.get(horario, '💊')
            st.markdown(f"""
            <div class="timing-card">
                <strong>{icone} {horario}</strong>
            </div>""", unsafe_allow_html=True)

            for supp in supps:
                dose_info = supp.get('dose_unidade', 'conforme prescrição')
                custo = supp.get('custo_medio', 0)
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"💊 **{supp['nome']}**")
                with col2:
                    st.write(f"_{dose_info}_")
                with col3:
                    st.write(f"R${custo:.0f}/mês")

            st.markdown("")

    # Notas importantes
    st.markdown("---")
    st.markdown("### 📌 Notas Importantes do Protocolo")

    notas_gerais = [
        "✅ Iniciar Berberina gradualmente: 500mg/dia (semana 1) → 1.000mg (semana 2) → 1.500mg (semana 3+)",
        "✅ Inulina: escalar 5g/dia (semana 1) → 10g → 15g (evitar gases)",
        "✅ Magnésio: 2/3 da dose à noite (melhora sono e cortisol)",
        "✅ Vitamina D + K2: sempre com refeição gordurosa (absorção 50% maior)",
        "✅ Probiótico: tomar 2-4h longe de antibióticos",
        "⚠️ Monitorar glicemia nas primeiras 2 semanas (potencialização)",
    ]

    for nota in notas_gerais:
        st.markdown(nota)


def render_exames_monitoramento(doenca_dados, perfil):
    """Exibe exames e metas de monitoramento"""
    st.markdown("### 🔬 Exames e Monitoramento")

    metas = doenca_dados.get('metas_terapeuticas', {})
    meta_id = doenca_dados['meta']['id']

    # Metas baseadas no perfil
    if meta_id == "DM2":
        hba1c_atual = perfil.get('hba1c', 8.0)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🎯 Metas Terapêuticas")

            dados_metas = [
                {"Marcador": "HbA1c", "Atual": f"{hba1c_atual}%",
                 "Meta Ótimo": f"{metas.get('HbA1c_otimo_pct', 6.0)}%",
                 "Meta Bom": f"{metas.get('HbA1c_bom_pct', 6.5)}%"},
                {"Marcador": "HOMA-IR", "Atual": f"{perfil.get('homa_ir', 5.0)}",
                 "Meta Ótimo": f"{metas.get('HOMA_IR_otimo', 1.5)}",
                 "Meta Bom": f"{metas.get('HOMA_IR_bom', 2.5)}"},
                {"Marcador": "Glicemia Jejum", "Atual": f"{perfil.get('glicemia', 140)} mg/dL",
                 "Meta Ótimo": f"{metas.get('glicemia_jejum_otimo_mgdl', 90)} mg/dL",
                 "Meta Bom": f"{metas.get('glicemia_jejum_bom_mgdl', 100)} mg/dL"},
                {"Marcador": "Vitamina D", "Atual": "A dosar",
                 "Meta Ótimo": f"{metas.get('VitD_otimo_ngml', 70)} ng/mL",
                 "Meta Bom": "60 ng/mL"},
                {"Marcador": "Magnésio sérico", "Atual": "A dosar",
                 "Meta Ótimo": f"{metas.get('Magnesio_otimo_mgdl', 2.2)} mg/dL",
                 "Meta Bom": "2.0 mg/dL"},
            ]

            st.dataframe(pd.DataFrame(dados_metas), use_container_width=True, hide_index=True)

        with col2:
            st.markdown("#### 📅 Cronograma de Exames")

            exames = doenca_dados.get('exames_baseline', [])
            if exames:
                dados_exames = []
                for ex in exames:
                    if ex.get('prioridade') in ['essencial', 'completo']:
                        dados_exames.append({
                            'Exame': ex['nome'],
                            'Frequência': ex.get('frequencia', 'anual'),
                            'Prioridade': ex.get('prioridade', '').title()
                        })

                if dados_exames:
                    st.dataframe(
                        pd.DataFrame(dados_exames),
                        use_container_width=True,
                        hide_index=True,
                        height=300
                    )

    # Alertas especiais
    alertas_especiais = doenca_dados.get('alertas_especiais', [])
    medicamentos = perfil.get('medicamentos', [])

    alertas_relevantes = []
    for alerta in alertas_especiais:
        cond = alerta.get('condicao', '')
        for med in medicamentos:
            if cond.lower() in med.lower() or med.lower() in cond.lower():
                alertas_relevantes.append(alerta)
                break

    if alertas_relevantes:
        st.markdown("#### 🚨 Alertas Específicos para Este Paciente")
        for alerta in alertas_relevantes:
            sev = alerta.get('severidade', 'moderada')
            if sev == 'alta' or sev == 'critica':
                st.error(f"🚨 {alerta['alerta']}")
            else:
                st.warning(f"⚠️ {alerta['alerta']}")


def render_sinergias_top(selecionados):
    """Exibe as melhores combinações sinérgicas"""
    st.markdown("### ✨ Melhores Sinergias do Protocolo")

    sinergias_encontradas = []
    ids_selecionados = {s['id'] for s in selecionados}

    for supp in selecionados:
        for sin in supp.get('sinergias', []):
            if sin['suplemento_id'] in ids_selecionados and sin.get('rating', 0) >= 4:
                sinergias_encontradas.append({
                    'Combinação': f"{supp['nome']} + {sin['suplemento_id'].replace('_', ' ').title()}",
                    'Rating Sinergia': get_stars(sin['rating']),
                    'Evidência': sin.get('evidencia', '-'),
                    'Benefício': sin.get('beneficio', '-')
                })

    if sinergias_encontradas:
        # Remover duplicatas
        vistos = set()
        unicos = []
        for sin in sinergias_encontradas:
            key = frozenset(sin['Combinação'].split(' + '))
            if key not in vistos:
                vistos.add(key)
                unicos.append(sin)

        st.dataframe(
            pd.DataFrame(unicos[:8]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Adicione mais suplementos ao protocolo para ver sinergias.")


def render_custo_detalhado(selecionados, custo_total, orcamento):
    """Análise de custo detalhada"""
    st.markdown("### 💰 Análise de Custo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Protocolo", f"R$ {custo_total:.0f}/mês")
    with col2:
        st.metric("Orçamento Disponível", f"R$ {orcamento}/mês")
    with col3:
        saldo = orcamento - custo_total
        st.metric("Saldo", f"R$ {saldo:.0f}", delta=f"{saldo:.0f}")

    # Gráfico de pizza por categoria
    if selecionados:
        dados_custo = {}
        for supp in selecionados:
            cat = supp.get('categoria', 'outro').replace('_', ' ').title()
            dados_custo[cat] = dados_custo.get(cat, 0) + supp.get('custo_medio', 0)

        df_custo = pd.DataFrame(
            list(dados_custo.items()),
            columns=['Categoria', 'Custo Mensal (R$)']
        ).sort_values('Custo Mensal (R$)', ascending=False)

        st.bar_chart(df_custo.set_index('Categoria'))

        # Tabela de custo por suplemento
        dados_lista = [
            {
                'Suplemento': s['nome'],
                'Prioridade': s.get('_prioridade', ''),
                'Custo Min': f"R$ {s.get('custo_min', 0):.0f}",
                'Custo Médio': f"R$ {s.get('custo_medio', 0):.0f}",
                'Custo Máx': f"R$ {s.get('custo_max', 0):.0f}"
            }
            for s in sorted(selecionados, key=lambda x: x.get('custo_medio', 0), reverse=True)
        ]
        st.dataframe(pd.DataFrame(dados_lista), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# APLICAÇÃO PRINCIPAL
# ══════════════════════════════════════════════════

def main():
    render_header()

    # Carregar doenças
    doencas = carregar_doencas()

    if not doencas:
        st.error("⚠️ Nenhuma doença encontrada! Verifique se a pasta 'data/' contém arquivos JSON.")
        st.info("Estrutura esperada:\n```\napp.py\ndata/\n  dm2.json\n  hipertensao.json\n  ...\n```")
        return

    # Formulário do paciente (sidebar)
    perfil = render_sidebar_form(doencas)

    if not perfil:
        return

    # Estado inicial sem protocolo gerado
    if not perfil.get('gerar') and 'protocolo_gerado' not in st.session_state:
        # Tela inicial
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("## Bem-vindo ao Sistema de Saúde Integrativa")
            st.markdown("""
            Este sistema gera **protocolos personalizados** de suplementação baseados em:
            - ✅ Evidências científicas (RCTs, Meta-análises)
            - ✅ Perfil clínico individual do paciente
            - ✅ Orçamento disponível
            - ✅ Medicamentos em uso (interações)
            - ✅ Complicações presentes

            **Como usar:**
            1. Preencha o perfil do paciente na barra lateral
            2. Informe os medicamentos em uso
            3. Defina o orçamento mensal
            4. Clique em **GERAR PROTOCOLO**
            """)

        with col2:
            st.markdown("### 📊 Doenças Disponíveis")
            for did, dados in doencas.items():
                prev = dados['meta'].get('prevalencia_brasil_pct', 0)
                st.markdown(f"- **{dados['meta']['nome']}** ({prev}% prevalência)")

        return

    # Gerar protocolo
    if perfil.get('gerar') or 'protocolo_gerado' in st.session_state:
        if perfil.get('gerar'):
            st.session_state['protocolo_gerado'] = perfil

        perfil_atual = st.session_state.get('protocolo_gerado', perfil)
        doenca_dados = perfil_atual['doenca_dados']

        # Resumo do paciente
        render_resumo_paciente(perfil_atual)

        # Identificar cenário
        cenario = identificar_cenario(
            doenca_dados,
            perfil_atual.get('hba1c', 7.0),
            perfil_atual.get('homa_ir', 5.0),
            perfil_atual.get('complicacoes', [])
        )

        # Gerar recomendações
        mecanismos_criticos = []
        if perfil_atual.get('homa_ir', 5) > 5:
            mecanismos_criticos.append('B1')
        if perfil_atual.get('hba1c', 7) > 8:
            mecanismos_criticos.extend(['B2', 'B3'])
        if perfil_atual.get('tgp', 35) > 40:
            mecanismos_criticos.extend(['B4', 'B5'])

        perfil_atual['mecanismos_criticos'] = mecanismos_criticos

        selecionados, excluidos, alertas, custo_total = gerar_recomendacoes(
            doenca_dados,
            cenario,
            perfil_atual['orcamento'],
            perfil_atual.get('medicamentos', []),
            perfil_atual.get('condicoes', []),
            perfil_atual
        )

        # Cenário identificado
        if cenario:
            st.info(
                f"📋 **Cenário Clínico:** {cenario.get('nome', 'Não identificado')} "
                f"— {cenario.get('descricao', '')}"
            )

        # Alertas de segurança
        render_alertas(alertas, excluidos)

        # Tabs principais
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💊 Recomendações",
            "⏰ Protocolo Diário",
            "✨ Sinergias",
            "💰 Custos",
            "🔬 Monitoramento"
        ])

        with tab1:
            render_lista_suplementos(selecionados, custo_total)

        with tab2:
            render_protocolo_diario(selecionados)

        with tab3:
            render_sinergias_top(selecionados)

        with tab4:
            render_custo_detalhado(selecionados, custo_total, perfil_atual['orcamento'])

        with tab5:
            render_exames_monitoramento(doenca_dados, perfil_atual)

    # Footer
    st.markdown("""
    <div class="footer-note">
        ⚕️ <strong>Uso Profissional:</strong> Este sistema é uma ferramenta de apoio clínico para profissionais de saúde
        habilitados. As recomendações devem ser avaliadas individualmente. Sempre considere o contexto clínico completo do paciente.
        Baseado em evidências científicas atualizadas até 2025. Não substitui avaliação médica.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
