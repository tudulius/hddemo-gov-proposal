import streamlit as st
from anthropic import Anthropic
from groq import Groq
import json
import PyPDF2
import io

st.set_page_config(
    page_title="정부지원과제 사업계획서 작성기",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 모델 설정
CLAUDE_MODELS = {
    "claude-3-opus-20240229": {
        "name": "Claude 3 Opus",
        "description": "가장 강력한 성능, 복잡한 작업에 적합",
        "max_tokens": 4000
    },
    "claude-3-sonnet-20240229": {
        "name": "Claude 3 Sonnet",
        "description": "균형 잡힌 성능과 속도",
        "max_tokens": 4000
    },
    "claude-3-haiku-20240229": {
        "name": "Claude 3 Haiku",
        "description": "빠른 속도, 간단한 작업에 적합",
        "max_tokens": 4000
    },
    "claude-3.5-sonnet": {
        "name": "Claude 3.5 Sonnet",
        "description": "향상된 성능의 Sonnet 모델, 복잡한 작업도 빠르게 처리",
        "max_tokens": 4000
    }
}

GROQ_MODELS = {
    "mixtral-8x7b-32768": {
        "name": "Mixtral 8x7B",
        "description": "최신 오픈소스 모델, 다양한 작업에 적합",
        "max_tokens": 4000
    },
    "llama2-70b-4096": {
        "name": "LLaMA 2 70B",
        "description": "안정적인 성능의 대형 모델",
        "max_tokens": 4000
    },
    "deepseek-r1-distill-qwen-32b": {
        "name": "DeepSeek R1 Distill QWAN",
        "description": "고성능 압축 모델, 빠른 응답 속도",
        "max_tokens": 4000
    },
    "qwan-2.5-coder-32b": {
        "name": "QWAN 2.5 Coder",
        "description": "코딩 특화 모델, 기술 문서 작성에 강점",
        "max_tokens": 4000
    }
}

# 사이드바 설정
with st.sidebar:
    st.title("🔧 설정")
    
    # LLM 선택
    llm_provider = st.radio(
        "AI 모델 제공자 선택",
        ["Claude", "Groq"],
        help="각 제공자별 특징:\n- Claude: 높은 품질의 텍스트 생성\n- Groq: 빠른 처리 속도"
    )
    
    if llm_provider == "Claude":
        # Claude API 키 입력 받기
        api_key = st.text_input("Claude API Key", type="password")
        if not api_key:
            st.info("Claude API 키를 입력해주세요.", icon="🗝️")
            st.stop()

        # Anthropic 클라이언트 생성
        try:
            client = Anthropic(api_key=api_key)
            model_options = list(CLAUDE_MODELS.keys())
            
            # 모델을 성능 순서대로 정렬
            model_order = {
                "claude-3-opus-20240229": 1,
                "claude-3.5-sonnet": 2,
                "claude-3-sonnet-20240229": 3,
                "claude-3-haiku-20240229": 4
            }
            model_options.sort(key=lambda x: model_order.get(x, 999))
            
            selected_model = st.selectbox(
                "Claude 모델 선택",
                model_options,
                format_func=lambda x: f"{CLAUDE_MODELS[x]['name']} - {CLAUDE_MODELS[x]['description']}",
                help="모델을 선택하세요. 위에서부터 성능이 좋은 순서입니다."
            )
            
            # 선택된 모델 정보 표시
            st.info(CLAUDE_MODELS[selected_model]["description"])
            
        except Exception as e:
            st.error(f"API 키가 올바르지 않거나 모델 목록을 가져오는데 실패했습니다: {str(e)}")
            st.stop()

    else:  # Groq
        # Groq API 키 입력 받기
        api_key = st.text_input("Groq API Key", type="password")
        if not api_key:
            st.info("Groq API 키를 입력해주세요.", icon="🗝️")
            st.stop()

        # Groq 클라이언트 생성
        try:
            client = Groq(api_key=api_key)
            model_options = list(GROQ_MODELS.keys())
            selected_model = st.selectbox(
                "Groq 모델 선택",
                model_options,
                format_func=lambda x: GROQ_MODELS[x]["name"],
                help="모델을 선택하세요"
            )
            
            # 선택된 모델 정보 표시
            st.info(GROQ_MODELS[selected_model]["description"])
            
        except Exception as e:
            st.error(f"API 키가 올바르지 않거나 모델 목록을 가져오는데 실패했습니다: {str(e)}")
            st.stop()
    
    # 고급 설정
    with st.expander("🛠️ 고급 설정"):
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="높을수록 더 창의적인 결과가 생성됩니다"
        )
        
        max_tokens = st.number_input(
            "최대 토큰 수",
            min_value=1000,
            max_value=4000,
            value=4000,
            step=500,
            help="생성될 텍스트의 최대 길이"
        )
    
    # 모델 정보 표시
    st.divider()
    st.markdown("### 선택된 모델 정보")
    model_info = CLAUDE_MODELS[selected_model] if llm_provider == "Claude" else GROQ_MODELS[selected_model]
    st.info(
        f"제공자: {llm_provider}\n"
        f"모델: {model_info['name']}\n"
        f"특징: {model_info['description']}"
    )

# 메인 화면
st.title("🏢 정부지원과제 사업계획서 작성기")
st.write(
    "공고문 PDF와 회사 정보를 입력하시면, AI가 맞춤형 사업계획서를 작성해드립니다. "
    "이 서비스를 이용하시려면 Claude 또는 Groq API 키가 필요합니다."
)

# PDF 파일 업로드
uploaded_file = st.file_uploader("공고문 PDF 파일을 업로드해주세요", type="pdf")
announcement_text = ""

if uploaded_file is not None:
    try:
        # PDF 파일 읽기
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        
        # 모든 페이지의 텍스트 추출
        announcement_text = ""
        for page in pdf_reader.pages:
            announcement_text += page.extract_text() + "\n"
        
        # 추출된 텍스트 미리보기 표시
        st.subheader("📄 추출된 공고문 내용")
        with st.expander("공고문 내용 보기"):
            st.text(announcement_text)
            
    except Exception as e:
        st.error(f"PDF 파일 처리 중 오류가 발생했습니다: {str(e)}")
        st.stop()

# 회사 정보 입력
st.subheader("회사 정보 입력")
col1, col2 = st.columns(2)

with col1:
    company_name = st.text_input("회사명")
    business_number = st.text_input("사업자등록번호")
    ceo_name = st.text_input("대표자명")
    establishment_date = st.date_input("설립일자")
    
with col2:
    employee_count = st.number_input("직원 수", min_value=1)
    annual_revenue = st.number_input("연간 매출액(백만원)", min_value=0)
    main_business = st.text_area("주요 사업내용", height=100)
    company_address = st.text_input("회사 주소")

if st.button("사업계획서 생성", type="primary"):
    if not (announcement_text and company_name and business_number and ceo_name and main_business):
        st.error("공고문 PDF와 모든 필수 항목을 입력해주세요.")
        st.stop()
        
    # 회사 정보 구조화
    company_info = {
        "회사명": company_name,
        "사업자등록번호": business_number,
        "대표자명": ceo_name,
        "설립일자": establishment_date.strftime("%Y-%m-%d"),
        "직원수": employee_count,
        "연간매출액": f"{annual_revenue}백만원",
        "주요사업내용": main_business,
        "회사주소": company_address
    }
    
    # 프롬프트 구성
    prompt = f"""아래의 정부지원과제 공고문과 회사 정보를 바탕으로 약 30페이지 분량의 상세한 사업계획서를 작성해주세요.

공고문:
{announcement_text}

회사 정보:
{json.dumps(company_info, ensure_ascii=False, indent=2)}

다음과 같은 구조로 사업계획서를 작성해주세요:

1. 사업 개요
2. 기업 현황
3. 사업 목표 및 내용
4. 추진 전략 및 방법
5. 사업 수행 체계
6. 기대효과
7. 소요예산
8. 향후 계획

각 섹션을 상세하게 작성하되, 공고문의 요구사항과 회사의 강점이 잘 부합되도록 작성해주세요.
특히 다음 사항들을 중점적으로 반영해주세요:
1. 공고문의 지원자격과 회사의 적격성
2. 공고문의 우대사항과 회사의 장점
3. 공고문의 평가기준과 회사의 강점
4. 지원금액 한도와 예산 계획의 적절성"""

    try:
        with st.spinner('사업계획서를 생성하고 있습니다... (약 2-3분 소요)'):
            if llm_provider == "Claude":
                # Claude API 호출
                message = client.messages.create(
                    model=selected_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                response_text = message.content[0].text
            else:
                # Groq API 호출
                completion = client.chat.completions.create(
                    model=selected_model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False
                )
                response_text = completion.choices[0].message.content
            
            # 결과를 탭으로 구분하여 표시
            tab1, tab2, tab3 = st.tabs(["📝 미리보기", "📊 분석", "⚙️ 설정"])
            
            with tab1:
                st.success("사업계획서가 생성되었습니다!")
                st.markdown(response_text)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    # 다운로드 버튼 (TXT)
                    st.download_button(
                        label="TXT 형식으로 다운로드",
                        data=response_text,
                        file_name=f"{company_name}_사업계획서.txt",
                        mime="text/plain"
                    )
                with col2:
                    # 마크다운 형식으로 다운로드
                    st.download_button(
                        label="마크다운 형식으로 다운로드",
                        data=response_text,
                        file_name=f"{company_name}_사업계획서.md",
                        mime="text/markdown"
                    )
                
            with tab2:
                st.subheader("공고문 분석 결과")
                analysis_prompt = f"""다음 공고문을 분석하여 핵심 요구사항들을 추출해주세요:
                1. 지원자격 요건
                2. 우대사항
                3. 평가 기준
                4. 지원금액 한도
                5. 주의사항
                
                공고문:
                {announcement_text}
                """
                
                if llm_provider == "Claude":
                    analysis = client.messages.create(
                        model=selected_model,
                        max_tokens=2000,
                        temperature=0.3,
                        messages=[{"role": "user", "content": analysis_prompt}]
                    )
                    analysis_text = analysis.content[0].text
                else:
                    analysis = client.chat.completions.create(
                        model=selected_model,
                        messages=[{"role": "user", "content": analysis_prompt}],
                        temperature=0.3,
                        max_tokens=2000,
                        stream=False
                    )
                    analysis_text = analysis.choices[0].message.content
                
                st.markdown(analysis_text)
            
            with tab3:
                st.subheader("생성 설정")
                st.json({
                    "AI 제공자": llm_provider,
                    "모델명": model_info["name"],
                    "모델 설명": model_info["description"],
                    "최대 토큰": max_tokens,
                    "Temperature": temperature
                })
            
    except Exception as e:
        st.error(f"사업계획서 생성 중 오류가 발생했습니다: {str(e)}")
        if "model_not_found" in str(e):
            st.warning("선택한 모델이 현재 사용 불가능합니다. 다른 모델을 선택해주세요.")
            st.info("사용 가능한 모델 목록을 확인 중입니다...")