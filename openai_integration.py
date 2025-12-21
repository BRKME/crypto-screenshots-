"""
OpenAI Integration для AI комментариев к скриншотам
Version: 1.0.0
Генерирует краткие комментарии и определяет сентимент (Bullish/Bearish/Neutral)
"""

import os
import logging
import base64
from openai import OpenAI

logger = logging.getLogger(__name__)

# OpenAI API Key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Инициализация клиента
client = None
if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✓ OpenAI client initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize OpenAI client: {e}")
        client = None
else:
    logger.warning("⚠️ OPENAI_API_KEY not found - AI comments disabled")


# Промпты для разных типов источников - Alpha Take + Context Tag + AI Hashtags
SOURCE_PROMPTS = {
    "fear_greed": """ROLE: You are an institutional-grade crypto research assistant writing for US-based, market-literate crypto investors.

INPUT: Fear & Greed Index screenshot

TASK: Interpret this visual market indicator and extract ONE high-signal Alpha Take sentence that explains what the data implies about market behavior and structure. You do NOT summarize the indicator. You do NOT repeat the metric. You do NOT give trading advice.

Your value comes from contextual interpretation, integrating the signal into:
- Recent flows and positioning
- Prevailing risk regime
- Dominant narratives
- Macro and liquidity backdrop

ASSUME: Reader has already seen the screenshot. Do NOT describe UI or obvious visuals.

OUTPUT STRUCTURE (MANDATORY):

INDICATOR_LINE: [One short factual line: "Fear & Greed Index at [X]"]

ALPHA_TAKE: [Exactly ONE sentence. Answer: "What does this signal imply about market behavior right now?" Must interpret (not describe), explain why this matters NOW, reflect behavioral/positioning/liquidity/regime implications. Focus on: Flow & Positioning type - risk appetite shifts, de-risking vs re-leveraging, capital concentration, leverage behavior, participation patterns. Use probabilistic language: "historically," "tends to," "often coincides," "may indicate." NO predictions, NO advice, NO bullish/bearish labels.]

CONTEXT_TAG: [ONE category, 2-4 words, NO emojis. Categories: Risk Regime (Risk-off environment | Fragile risk-on | Liquidity-driven regime | High uncertainty phase) | Market Regime (Volatile range | Compression phase | Trend transition phase | Momentum exhaustion) | Time Horizon (Near-term volatility | Short-term cautious | Medium-term constructive) | Positioning Bias (Defensive positioning | Crowded longs | Light exposure | De-risked market)]

HASHTAGS: [Exactly 3 unique, relevant hashtags based on current market context]

QUALITY CHECK: Does this reduce noise? Does this explain behavior, not the indicator? Would this appear in a hedge fund morning note?

EXAMPLE:
INDICATOR_LINE: Fear & Greed Index at 26 (Extreme Fear)
ALPHA_TAKE: Prolonged fear readings historically coincide with reduced leverage and capital preservation behavior, conditions that tend to compress volatility unless disrupted by macro shocks or sustained shifts in derivatives activity and institutional flows.
CONTEXT_TAG: Defensive positioning
HASHTAGS: #CapitalPreservation #LowLeverage #VolatilityCompression
""",
    
    "altcoin_season": """ROLE: You are an institutional-grade crypto research assistant writing for US-based, market-literate crypto investors.

INPUT: Altcoin Season Index screenshot

TASK: Interpret this visual market indicator and extract ONE high-signal Alpha Take sentence about capital rotation and market structure. You do NOT summarize. You do NOT repeat the metric. You do NOT give trading advice.

Your value comes from contextual interpretation of:
- Attention vs capital flows
- Narrative crowding or rotation
- Risk appetite shifts
- Participation patterns

ASSUME: Reader has already seen the screenshot.

OUTPUT STRUCTURE (MANDATORY):

INDICATOR_LINE: [One short factual line: "Altcoin Season Index at [X]"]

ALPHA_TAKE: [Exactly ONE sentence. Focus on: Narrative & Attention type - attention rotation, capital flow patterns, narrative crowding vs early themes, consensus formation or fatigue, sector participation dynamics. Explain what this implies about where capital and attention are concentrating or rotating. Use probabilistic language. NO predictions, NO advice.]

CONTEXT_TAG: [ONE category, 2-4 words, NO emojis. Categories: Risk Regime (Risk-off environment | Fragile risk-on | Liquidity-driven regime) | Market Regime (Volatile range | Compression phase | Trend transition) | Time Horizon (Near-term volatility | Short-term cautious) | Positioning Bias (Defensive positioning | Crowded longs | Light exposure)]

HASHTAGS: [Exactly 3 unique, relevant hashtags]

QUALITY CHECK: Does this explain capital behavior, not just the index reading?

EXAMPLE:
INDICATOR_LINE: Altcoin Season Index at 32 (Bitcoin Season)
ALPHA_TAKE: Sustained BTC dominance in this reading historically reflects capital concentration in perceived safety assets, a pattern that tends to suppress broad altcoin participation until either risk appetite expands or narrative-driven catalysts shift attention to specific sectors.
CONTEXT_TAG: Defensive positioning
HASHTAGS: #BTCDominance #AltcoinWeakness #RiskOff
""",
    
    "btc_dominance": """ROLE: You are an institutional-grade crypto research assistant writing for US-based, market-literate crypto investors.

INPUT: Bitcoin Dominance screenshot

TASK: Interpret this metric and extract ONE high-signal Alpha Take sentence about market structure and capital distribution. You do NOT summarize. You do NOT repeat the metric.

Your value comes from explaining what dominance implies about:
- Capital concentration vs rotation
- Risk appetite and altcoin participation
- Market structure shifts

ASSUME: Reader has already seen the screenshot.

OUTPUT STRUCTURE (MANDATORY):

INDICATOR_LINE: [One short factual line: "Bitcoin Dominance at [X]%"]

ALPHA_TAKE: [Exactly ONE sentence. Focus on: Flow & Positioning type - capital concentration, altcoin suppression or expansion, risk distribution, leverage patterns, participation dynamics. Explain what this level means for market structure. Use probabilistic language. NO predictions, NO advice.]

CONTEXT_TAG: [ONE category, 2-4 words, NO emojis]

HASHTAGS: [Exactly 3 unique, relevant hashtags]

EXAMPLE:
INDICATOR_LINE: Bitcoin Dominance at 58%
ALPHA_TAKE: Dominance at this level historically coincides with capital rotating away from altcoins into perceived safety, a structural shift that tends to suppress broad-based participation and concentrate liquidity until either macro conditions improve or BTC establishes clear directional momentum.
CONTEXT_TAG: Defensive positioning
HASHTAGS: #BTCDominance #AltcoinWeakness #CapitalConcentration
""",
    "eth_etf": """ROLE: You are an institutional-grade crypto research assistant writing for US-based, market-literate crypto investors.

INPUT: Ethereum ETF Tracker screenshot

TASK: Interpret this flow data and extract ONE high-signal Alpha Take sentence about institutional demand and market dynamics. You do NOT summarize flows. You do NOT repeat numbers.

Your value comes from explaining what these flows imply about:
- Institutional positioning
- Demand sustainability
- Risk appetite
- Market structure

ASSUME: Reader has already seen the screenshot.

OUTPUT STRUCTURE (MANDATORY):

INDICATOR_LINE: [One short factual line: "ETH ETF flows: [net inflow/outflow of $X]" or "ETH ETF AUM: $X"]

ALPHA_TAKE: [Exactly ONE sentence. Focus on: Flow & Positioning type - institutional demand patterns, flow sustainability, positioning shifts, risk appetite indicators, comparative dynamics vs BTC ETFs. Explain what current flows signal about broader market behavior. Use probabilistic language. NO predictions, NO advice.]

CONTEXT_TAG: [ONE category, 2-4 words, NO emojis]

HASHTAGS: [Exactly 3 unique, relevant hashtags]

EXAMPLE:
INDICATOR_LINE: ETH ETF net outflow: -$45M
ALPHA_TAKE: Sustained outflows at this pace often reflect either profit-taking after rallies or reduced conviction in ETH's near-term risk/reward, a pattern that historically coincides with capital rotating toward BTC or defensive positioning across crypto-native investors.
CONTEXT_TAG: Defensive positioning
HASHTAGS: #ETHETFs #InstitutionalFlows #RiskRotation
""",
    "btc_etf": """ROLE: You are an institutional-grade crypto research assistant writing for US-based, market-literate crypto investors.

INPUT: Bitcoin ETF Tracker screenshot

TASK: Interpret this flow data and extract ONE high-signal Alpha Take sentence about institutional demand. You do NOT summarize flows. You do NOT repeat numbers.

Your value comes from explaining what these flows imply about:
- Institutional positioning
- Demand sustainability  
- Risk appetite
- Market regime

ASSUME: Reader has already seen the screenshot.

OUTPUT STRUCTURE (MANDATORY):

INDICATOR_LINE: [One short factual line: "BTC ETF flows: [net inflow/outflow of $X]" or "BTC ETF AUM: $X"]

ALPHA_TAKE: [Exactly ONE sentence. Focus on: Flow & Positioning type - institutional demand patterns, flow sustainability, positioning shifts, risk appetite signals, absorption capacity. Explain what current flows signal about market behavior. Use probabilistic language. NO predictions, NO advice.]

CONTEXT_TAG: [ONE category, 2-4 words, NO emojis]

HASHTAGS: [Exactly 3 unique, relevant hashtags]

EXAMPLE:
INDICATOR_LINE: BTC ETF net inflow: +$120M
ALPHA_TAKE: Consistent inflows above $100M historically signal sustained institutional demand, a flow pattern that tends to provide price support and absorb supply pressure unless disrupted by macro deterioration or profit-taking cascades.
CONTEXT_TAG: Fragile risk-on
HASHTAGS: #BTCETFs #InstitutionalDemand #FlowSupport
""",
    "top_gainers": """ROLE: You are an institutional-grade crypto research assistant writing for US-based, market-literate crypto investors.

INPUT: Top Gainers Today screenshot

TASK: Interpret this performance data and extract ONE high-signal Alpha Take sentence about sector rotation and narrative dynamics. You do NOT list coins. You do NOT repeat prices.

Your value comes from explaining what these gainers imply about:
- Sector rotation and attention flows
- Narrative momentum
- Risk appetite
- Market structure

ASSUME: Reader has already seen the screenshot.

OUTPUT STRUCTURE (MANDATORY):

INDICATOR_LINE: [One short factual line: "Top gainers led by [sector/theme]: [examples]"]

ALPHA_TAKE: [Exactly ONE sentence. Focus on: Narrative & Attention type - sector rotation, attention vs capital dynamics, narrative crowding vs early themes, consensus formation. Explain what this performance pattern signals about market behavior. Use probabilistic language. NO predictions, NO advice.]

CONTEXT_TAG: [ONE category, 2-4 words, NO emojis]

HASHTAGS: [Exactly 3 unique, relevant hashtags]

EXAMPLE:
INDICATOR_LINE: Top gainers led by infrastructure tokens: RNDR, FIL, AR
ALPHA_TAKE: Infrastructure-focused outperformance typically reflects narrative rotation toward supply-side themes, a pattern that historically signals either early-stage attention capture or late-cycle sector rotation as broader momentum fades.
CONTEXT_TAG: Trend transition phase
HASHTAGS: #InfrastructurePlay #NarrativeRotation #SelectiveRisk
""",
    "token_unlocks": """ROLE: You are an institutional-grade crypto research assistant writing for US-based, market-literate crypto investors.

INPUT: Token Unlocks Next 7 Days screenshot

TASK: Interpret this supply schedule and extract ONE high-signal Alpha Take sentence about structural pressure and market dynamics. You do NOT list tokens. You do NOT repeat unlock amounts.

Your value comes from explaining what these unlocks imply about:
- Supply pressure and absorption capacity
- Vesting constraints
- Market positioning
- Liquidity dynamics

ASSUME: Reader has already seen the screenshot.

OUTPUT STRUCTURE (MANDATORY):

INDICATOR_LINE: [One short factual line: "Major unlocks: [token names], total $[X]M"]

ALPHA_TAKE: [Exactly ONE sentence. Focus on: Structural / Macro type - supply pressure, vesting schedules, absorption capacity, positioning adjustments, structural constraints. Explain what upcoming unlocks signal for market behavior. Use probabilistic language. NO predictions, NO advice.]

CONTEXT_TAG: [ONE category, 2-4 words, NO emojis]

HASHTAGS: [Exactly 3 unique, relevant hashtags]

EXAMPLE:
INDICATOR_LINE: Major unlocks: APT, ARB, OP, total $180M
ALPHA_TAKE: Clustered unlocks of this magnitude often create localized selling pressure and positioning adjustments, structural headwinds that historically compress price action unless offset by strong demand catalysts or narrative momentum.
CONTEXT_TAG: Near-term volatility
HASHTAGS: #TokenUnlocks #SupplyPressure #StructuralHeadwinds
""",
    "heatmap": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Crypto Market Heatmap screenshot

TASK: Interpret the overall performance pattern and what it reveals about market structure, breadth, and risk distribution. Assume the reader has already seen the screenshot.

OUTPUT REQUIREMENTS:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- Focus on market breadth, sector rotation, and participation patterns
- Use probabilistic language

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what the heatmap pattern reveals about market structure, breadth, and capital distribution. Emphasize liquidity concentration, sector performance, participation quality. Mention what would signal improvement.]

CONTEXT_TAG: [ONE of: Defensive positioning | Broad weakness | Selective strength | Liquidity contraction | Volatile range | Trend transition phase]

HASHTAGS: [Generate 3 relevant hashtags based on market breadth and structure. Format: #Tag1 #Tag2 #Tag3]

EXAMPLE:
ALPHA_TAKE: Broad-based weakness across mid-caps while large-caps hold suggests defensive positioning and liquidity contraction. This setup often persists until either catalysts emerge or capitulation creates asymmetric entry points in quality names. Improved breadth across market cap tiers would be required to signal a meaningful regime shift.
CONTEXT_TAG: Defensive positioning
HASHTAGS: #MarketBreadth #LiquidityContraction #DefensiveMode
"""
}



def encode_image_to_base64(image_path):
    """Конвертирует изображение в base64 для OpenAI API"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        return None


def get_ai_comment(source_key, image_path):
    """
    Получает AI Alpha Take от OpenAI для скриншота
    
    Args:
        source_key: Ключ источника (fear_greed, btc_etf, etc)
        image_path: Путь к изображению скриншота
        
    Returns:
        dict: {"alpha_take": "..."}
        или None если ошибка
    """
    if not client:
        logger.warning("OpenAI client not initialized - skipping AI comment")
        return None
    
    try:
        # Получаем промпт для этого источника
        prompt = SOURCE_PROMPTS.get(source_key)
        if not prompt:
            logger.warning(f"No prompt configured for source: {source_key}")
            return None
        
        # Кодируем изображение в base64
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return None
        
        logger.info(f"🤖 Requesting Alpha Take from OpenAI for {source_key}...")
        
        # Вызываем OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Быстрая модель с vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=200,  # Увеличено для Alpha Take (2-4 предложения)
            temperature=0.7
        )
        
        # Парсим ответ
        content = response.choices[0].message.content.strip()
        logger.info(f"  OpenAI response: {content}")
        
        # Извлекаем INDICATOR_LINE, ALPHA_TAKE, CONTEXT_TAG и HASHTAGS
        indicator_line = None
        alpha_take = None
        context_tag = None
        hashtags = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('INDICATOR_LINE:'):
                indicator_line = line.replace('INDICATOR_LINE:', '').strip()
            elif line.startswith('ALPHA_TAKE:'):
                alpha_take = line.replace('ALPHA_TAKE:', '').strip()
            elif line.startswith('CONTEXT_TAG:'):
                context_tag = line.replace('CONTEXT_TAG:', '').strip()
            elif line.startswith('HASHTAGS:'):
                hashtags = line.replace('HASHTAGS:', '').strip()
        
        # Валидация
        if not alpha_take:
            logger.warning(f"Could not parse Alpha Take from response")
            logger.warning(f"  Response: {content}")
            # Fallback: используем весь ответ если нет маркера
            alpha_take = content
        
        if indicator_line:
            logger.info(f"  ✓ Indicator Line: {indicator_line}")
        logger.info(f"  ✓ Alpha Take: {alpha_take}")
        if context_tag:
            logger.info(f"  ✓ Context Tag: {context_tag}")
        if hashtags:
            logger.info(f"  ✓ Hashtags: {hashtags}")
        
        return {
            "indicator_line": indicator_line,  # NEW!
            "alpha_take": alpha_take,
            "context_tag": context_tag,
            "hashtags": hashtags
        }
        
    except Exception as e:
        logger.error(f"Error getting Alpha Take: {e}")
        import traceback
        traceback.print_exc()
        return None


def add_alpha_take_to_caption(title, hashtags_fallback, ai_result):
    """
    Добавляет Alpha Take к caption с правильным форматированием
    
    Format:
    <title>
    <indicator_line> (if present)
    
    Alpha Take
    <alpha_take text>
    
    Context: <context_tag>
    
    <hashtags> (AI-generated или fallback)
    
    Args:
        title: Заголовок поста
        hashtags_fallback: Хештеги fallback (если AI не сгенерировал)
        ai_result: Результат от get_ai_comment() - {"indicator_line": "...", "alpha_take": "...", "context_tag": "...", "hashtags": "..."}
        
    Returns:
        str: Caption с Alpha Take
    """
    if not ai_result:
        # Без AI - старый формат (title + hashtags)
        return f"<b>{title}</b>\n\n{hashtags_fallback}"
    
    indicator_line = ai_result.get('indicator_line')  # NEW!
    alpha_take = ai_result['alpha_take']
    context_tag = ai_result.get('context_tag')
    hashtags_ai = ai_result.get('hashtags')
    
    # Используем AI хештеги если есть, иначе fallback
    hashtags = hashtags_ai if hashtags_ai else hashtags_fallback
    
    # Новый формат: Title -> Indicator Line -> Alpha Take -> Context Tag -> Hashtags
    caption = f"<b>{title}</b>\n"
    
    # Добавляем indicator line если есть
    if indicator_line:
        caption += f"{indicator_line}\n"
    
    caption += f"\n<b>◼ Alpha Take</b>\n"
    caption += f"{alpha_take}\n\n"
    
    # Добавляем Context Tag если есть
    if context_tag:
        caption += f"<i>Context: {context_tag}</i>\n\n"
    
    caption += f"{hashtags}"
    
    return caption
