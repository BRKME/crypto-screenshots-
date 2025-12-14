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
    "fear_greed": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Fear & Greed Index screenshot

TASK: Interpret the visual indicator and extract a concise Alpha Take that explains what the data reflects about market behavior and structure, not what to do. This format is interpretive, not news-driven.

ASSUME: The reader has already seen the screenshot. Do not describe obvious visuals or UI elements.

OUTPUT REQUIREMENTS:
- Clear, concise, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis
- Focus on market state, behavior, structure, and regimes
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"
- Goal: contextual understanding, not persuasion, signaling, or prediction

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences interpreting what the metric signals about sentiment, positioning, liquidity preference, participation, or risk appetite. Emphasize second-order effects like leverage behavior, capital concentration. If relevant, mention what would need to change for the takeaway to shift. NO calls to action, NO strategy language.]

CONTEXT_TAG: [ONE of: Risk-off environment | Selective risk-on | High uncertainty phase | Defensive positioning | Crowded longs | Short-term cautious | Volatile range | Near-term volatility]

HASHTAGS: [Generate 3 relevant, contextual hashtags based on the current market state. Use professional vocabulary. Format: #Tag1 #Tag2 #Tag3]

TONE: Analytical, neutral, institutional. Think: sell-side market note, not social media commentary. Data > emotion. Clarity > confidence.

DO NOT:
- Repeat the metric mechanically
- Predict price direction
- Use absolutes or certainty
- Add strategy or execution hints ("accumulate," "wait," "buy dips")

QUALITY CHECK:
- Does this add interpretation, not description?
- Does it help the reader orient within the current market regime?
- Does it avoid implying a trade, bias, or directional view?

EXAMPLE:
ALPHA_TAKE: Prolonged fear readings typically coincide with reduced leverage, lower participation, and capital preservation behavior. Historically, such conditions compress volatility over time unless disrupted by macro or liquidity shocks. A sustained shift in derivatives activity or ETF flows would be required to meaningfully alter this sentiment backdrop.
CONTEXT_TAG: Defensive positioning
HASHTAGS: #CapitalPreservation #LowLeverage #FearZone
""",
    
    "altcoin_season": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Altcoin Season Index screenshot

TASK: Interpret the visual indicator and extract a concise Alpha Take about capital rotation and market structure. Assume the reader has already seen the screenshot.

OUTPUT REQUIREMENTS:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- Focus on capital flows, participation patterns, and regime shifts
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what the index reading means for market rotation, risk appetite, and capital distribution. Focus on second-order effects like altcoin suppression, Bitcoin concentration. Mention conditions that would shift this regime.]

CONTEXT_TAG: [ONE of: Risk-off environment | Selective risk-on | Bitcoin-led regime | Altcoin expansion phase | Defensive positioning | Fragile risk-on | Short-term cautious]

HASHTAGS: [Generate 3 relevant hashtags based on current rotation dynamics. Format: #Tag1 #Tag2 #Tag3]

EXAMPLE:
ALPHA_TAKE: Readings below 25 indicate capital is rotating into Bitcoin, often reflecting risk-off sentiment within crypto. Historically, sustained Bitcoin dominance has preceded either broader market weakness or accumulation phases before the next alt cycle. This pattern tends to persist until macro clarity improves or BTC establishes a clearer directional trend.
CONTEXT_TAG: Risk-off environment
HASHTAGS: #BitcoinDominance #AltcoinSuppression #CapitalRotation
""",
    
    "btc_dominance": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Bitcoin Dominance screenshot

TASK: Interpret dominance levels and what they signal about market structure and capital distribution. Assume the reader has already seen the screenshot.

OUTPUT REQUIREMENTS:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- Focus on capital rotation, risk distribution, and market structure
- Use probabilistic language

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what current dominance means for market structure, capital flows, and risk appetite. Emphasize second-order effects like altcoin participation, leverage distribution. Mention what would shift this dynamic.]

CONTEXT_TAG: [ONE of: Risk-off environment | Selective risk-on | Defensive positioning | Bitcoin-led regime | Trend transition phase | De-risked market]

HASHTAGS: [Generate 3 relevant hashtags based on dominance level and market structure. Format: #Tag1 #Tag2 #Tag3]

EXAMPLE:
ALPHA_TAKE: Bitcoin dominance near 60% typically signals risk-off behavior within crypto, with capital flowing into the perceived safety of BTC. This environment often persists until macro clarity improves or BTC itself establishes a clearer trend. Meaningful rotation back to alts would require both stable BTC price action and improved risk appetite indicators.
CONTEXT_TAG: Risk-off environment
HASHTAGS: #BTCDominance #SafeHaven #RiskOff
""",
    
    "eth_etf": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Ethereum ETF flows screenshot

TASK: Interpret flow patterns and what they signal about institutional demand dynamics. Assume the reader has already seen the screenshot.

OUTPUT REQUIREMENTS:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- Focus on flow trends, institutional behavior, and demand sustainability
- Use probabilistic language

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what the flow patterns indicate about institutional appetite, demand sustainability, and positioning. Emphasize second-order effects like liquidity conditions, structural demand. Mention what would invalidate this reading.]

CONTEXT_TAG: [ONE of: Light exposure | Cautious institutions | Flow reversal phase | Demand compression | Medium-term constructive | Short-term cautious]

HASHTAGS: [Generate 3 relevant hashtags based on ETF flow dynamics. Format: #Tag1 #Tag2 #Tag3]

EXAMPLE:
ALPHA_TAKE: Mixed daily flows with negative monthly performance suggest institutions remain cautious on ETH exposure. This consolidation pattern often precedes either a catalyst-driven shift or extended sideways action until fundamentals re-rate. Sustained positive weekly flows would be needed to signal a meaningful change in institutional positioning.
CONTEXT_TAG: Short-term cautious
HASHTAGS: #ETHFlows #InstitutionalCaution #DemandConsolidation
""",
    
    "btc_etf": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Bitcoin ETF flows screenshot

TASK: Interpret flow trends and what they reveal about institutional demand and market positioning. Assume the reader has already seen the screenshot.

OUTPUT REQUIREMENTS:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- Focus on demand dynamics, flow sustainability, and institutional behavior
- Use probabilistic language

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what flow patterns signal about institutional appetite and demand sustainability. Emphasize liquidity conditions, structural vs tactical demand. Mention reversal conditions.]

CONTEXT_TAG: [ONE of: Renewed demand | Flow reversal | Cautious institutions | Medium-term constructive | Compression phase | Light exposure]

HASHTAGS: [Generate 3 relevant hashtags based on BTC ETF flow trends. Format: #Tag1 #Tag2 #Tag3]

EXAMPLE:
ALPHA_TAKE: Sustained positive inflows after a period of outflows typically signal renewed institutional interest, though the magnitude matters more than direction alone. If this trend continues alongside improving macro conditions, it could support a more constructive setup. Reversal back to consistent outflows would invalidate this tentative shift in institutional sentiment.
CONTEXT_TAG: Renewed demand
HASHTAGS: #BTCFlows #InstitutionalDemand #FlowReversal
""",
    
    "top_gainers": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Top Gainers screenshot

TASK: Interpret which tokens are gaining and what this reveals about market themes, rotation, and participation patterns. Assume the reader has already seen the screenshot.

OUTPUT REQUIREMENTS:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- Focus on rotation patterns, sector strength, and participation breadth
- Use probabilistic language

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what the gaining tokens reveal about market themes, capital rotation, and risk appetite. Emphasize narrative strength, speculation vs fundamentals, participation breadth. Mention what would signal a regime shift.]

CONTEXT_TAG: [ONE of: Selective risk-on | Narrative rotation | Speculation phase | Broad participation | Fragile risk-on | High uncertainty phase]

HASHTAGS: [Generate 3 relevant hashtags based on which sectors/narratives are gaining. Format: #Tag1 #Tag2 #Tag3]

EXAMPLE:
ALPHA_TAKE: Multiple double-digit gainers across infrastructure tokens suggest rotation into fundamental-driven narratives rather than pure speculation. This pattern often emerges when risk appetite is improving but not yet fully extended, favoring selective positioning over broad exposure. A shift to meme or low-cap dominance would signal different market dynamics.
CONTEXT_TAG: Selective risk-on
HASHTAGS: #InfrastructurePlay #NarrativeRotation #SelectiveRisk
""",
    
    "token_unlocks": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Token Unlocks screenshot

TASK: Interpret upcoming unlocks and their potential impact on supply dynamics and market positioning. Assume the reader has already seen the screenshot.

OUTPUT REQUIREMENTS:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- Focus on supply pressure, market absorption capacity, and positioning effects
- Use probabilistic language

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining the potential impact of upcoming unlocks on supply dynamics and market behavior. Emphasize absorption capacity, frontrunning behavior, holder incentives. Mention key variables that matter.]

CONTEXT_TAG: [ONE of: Supply pressure | Well-telegraphed event | Frontrun positioning | Manageable unlock | High uncertainty phase | Near-term volatility]

HASHTAGS: [Generate 3 relevant hashtags based on unlock size and market impact. Format: #Tag1 #Tag2 #Tag3]

EXAMPLE:
ALPHA_TAKE: Upcoming cliff unlocks totaling $98M are significant but manageable given current market depth. Historically, well-telegraphed unlocks see selling pressure frontrun, with actual unlock dates often marking local lows if broader market conditions hold. The key variable is whether holders choose immediate liquidity or structured distribution.
CONTEXT_TAG: Well-telegraphed event
HASHTAGS: #TokenUnlocks #SupplyPressure #VestingSchedule
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
        
        # Извлекаем ALPHA_TAKE, CONTEXT_TAG и HASHTAGS
        alpha_take = None
        context_tag = None
        hashtags = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('ALPHA_TAKE:'):
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
        
        logger.info(f"  ✓ Alpha Take: {alpha_take}")
        if context_tag:
            logger.info(f"  ✓ Context Tag: {context_tag}")
        if hashtags:
            logger.info(f"  ✓ Hashtags: {hashtags}")
        
        return {
            "alpha_take": alpha_take,
            "context_tag": context_tag,  # Может быть None
            "hashtags": hashtags  # Может быть None (NEW!)
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
    
    Alpha Take
    <alpha_take text>
    
    Context: <context_tag>
    
    <hashtags> (AI-generated или fallback)
    
    Args:
        title: Заголовок поста
        hashtags_fallback: Хештеги fallback (если AI не сгенерировал)
        ai_result: Результат от get_ai_comment() - {"alpha_take": "...", "context_tag": "...", "hashtags": "..."}
        
    Returns:
        str: Caption с Alpha Take
    """
    if not ai_result:
        # Без AI - старый формат (title + hashtags)
        return f"<b>{title}</b>\n\n{hashtags_fallback}"
    
    alpha_take = ai_result['alpha_take']
    context_tag = ai_result.get('context_tag')  # Может быть None
    hashtags_ai = ai_result.get('hashtags')  # Может быть None (NEW!)
    
    # Используем AI хештеги если есть, иначе fallback
    hashtags = hashtags_ai if hashtags_ai else hashtags_fallback
    
    # Новый формат: Title -> Alpha Take -> Alpha take text -> Context Tag (if exists) -> Hashtags
    caption = f"<b>{title}</b>\n\n"
    caption += f"<b>Alpha Take</b>\n"
    caption += f"{alpha_take}\n\n"
    
    # Добавляем Context Tag если есть
    if context_tag:
        caption += f"<i>Context: {context_tag}</i>\n\n"
    
    caption += f"{hashtags}"
    
    return caption
