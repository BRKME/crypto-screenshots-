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


# Промпты для разных типов источников - Alpha Take + Context Tag Style
SOURCE_PROMPTS = {
    "fear_greed": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Fear & Greed Index screenshot

TASK: Interpret the visual indicator and extract a concise Alpha Take that explains what the data reflects about market behavior.

RULES:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis, NO hashtags
- Focus on market state, behavior, and regimes
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"
- Goal: contextual understanding, not persuasion

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what this metric signals about sentiment, positioning, or regime. Emphasize second-order effects (liquidity, participation, risk appetite)]

CONTEXT_TAG: [ONE of: Risk-off environment | Selective risk-on | High uncertainty phase | Defensive positioning | Crowded longs | Short-term cautious | Volatile range | Near-term volatility]

EXAMPLE:
ALPHA_TAKE: Prolonged fear readings typically coincide with reduced leverage, lower participation, and capital preservation behavior. Historically, such conditions compress volatility over time unless disrupted by macro or liquidity shocks. A shift in derivatives activity or ETF flows would be required to meaningfully alter this sentiment backdrop.
CONTEXT_TAG: Defensive positioning
""",
    
    "altcoin_season": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Altcoin Season Index screenshot

TASK: Interpret the visual indicator and extract a concise Alpha Take about capital rotation and market participation.

RULES:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis, NO hashtags
- Focus on capital flows and regime shifts
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what the index reading means for market rotation and risk appetite. Focus on capital flows between BTC and alts]

CONTEXT_TAG: [ONE of: Risk-off environment | Selective risk-on | Bitcoin-led regime | Altcoin expansion phase | Defensive positioning | Fragile risk-on | Short-term cautious]

EXAMPLE:
ALPHA_TAKE: Readings below 25 indicate capital is rotating into Bitcoin, often reflecting risk-off sentiment within crypto. Historically, sustained Bitcoin dominance has preceded either broader market weakness or accumulation phases before the next alt cycle. This pattern tends to persist until macro clarity improves or BTC establishes a clearer directional trend.
CONTEXT_TAG: Risk-off environment
""",
    
    "btc_dominance": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Bitcoin Dominance screenshot

TASK: Interpret dominance levels and what they signal about market structure and risk appetite.

RULES:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis, NO hashtags
- Focus on capital rotation and risk distribution
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what current dominance means for market structure, capital flows, and risk appetite across crypto]

CONTEXT_TAG: [ONE of: Risk-off environment | Selective risk-on | Defensive positioning | Bitcoin-led regime | Trend transition phase | De-risked market]

EXAMPLE:
ALPHA_TAKE: Bitcoin dominance near 60% typically signals risk-off behavior within crypto, with capital flowing into the perceived safety of BTC. This environment often persists until macro clarity improves or BTC itself establishes a clearer trend. Meaningful rotation back to alts would require both stable BTC price action and improved risk appetite indicators.
CONTEXT_TAG: Risk-off environment
""",
    
    "eth_etf": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Ethereum ETF flows screenshot

TASK: Interpret flow patterns and what they signal about institutional demand dynamics.

RULES:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis, NO hashtags
- Focus on flow trends, demand signals, and institutional behavior
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what the flow patterns indicate about institutional appetite, demand sustainability, and market positioning]

CONTEXT_TAG: [ONE of: Light exposure | Cautious institutions | Flow reversal phase | Demand compression | Medium-term constructive | Short-term cautious]

EXAMPLE:
ALPHA_TAKE: Mixed daily flows with negative monthly performance suggest institutions remain cautious on ETH exposure. This consolidation pattern often precedes either a catalyst-driven shift or extended sideways action until fundamentals re-rate. Sustained positive weekly flows would be needed to signal a meaningful change in institutional positioning.
CONTEXT_TAG: Short-term cautious
""",
    
    "btc_etf": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Bitcoin ETF flows screenshot

TASK: Interpret flow trends and what they reveal about institutional demand and market positioning.

RULES:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis, NO hashtags
- Focus on demand dynamics, flow sustainability, and institutional behavior
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what flow patterns signal about institutional appetite and demand sustainability]

CONTEXT_TAG: [ONE of: Renewed demand | Flow reversal | Cautious institutions | Medium-term constructive | Compression phase | Light exposure]

EXAMPLE:
ALPHA_TAKE: Sustained positive inflows after a period of outflows typically signal renewed institutional interest, though the magnitude matters more than direction alone. If this trend continues alongside improving macro conditions, it could support a more constructive setup. Reversal back to consistent outflows would invalidate this tentative shift in institutional sentiment.
CONTEXT_TAG: Renewed demand
""",
    
    "top_gainers": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Top Gainers screenshot

TASK: Interpret which tokens are gaining and what this reveals about market themes, rotation, and risk appetite.

RULES:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis, NO hashtags
- Focus on rotation patterns, sector strength, and participation breadth
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what the gaining tokens reveal about market themes, capital rotation, and risk appetite]

CONTEXT_TAG: [ONE of: Selective risk-on | Narrative rotation | Speculation phase | Broad participation | Fragile risk-on | High uncertainty phase]

EXAMPLE:
ALPHA_TAKE: Multiple double-digit gainers across infrastructure tokens suggest rotation into fundamental-driven narratives rather than pure speculation. This pattern often emerges when risk appetite is improving but not yet fully extended, favoring selective positioning over broad exposure. A shift to meme or low-cap dominance would signal different market dynamics.
CONTEXT_TAG: Selective risk-on
""",
    
    "token_unlocks": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Token Unlocks screenshot

TASK: Interpret upcoming unlocks and their potential impact on supply dynamics and market positioning.

RULES:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis, NO hashtags
- Focus on supply pressure, market absorption capacity, and positioning effects
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining the potential impact of upcoming unlocks on supply dynamics and market behavior]

CONTEXT_TAG: [ONE of: Supply pressure | Well-telegraphed event | Frontrun positioning | Manageable unlock | High uncertainty phase | Near-term volatility]

EXAMPLE:
ALPHA_TAKE: Upcoming cliff unlocks totaling $98M are significant but manageable given current market depth. Historically, well-telegraphed unlocks see selling pressure frontrun, with actual unlock dates often marking local lows if broader market conditions hold. The key variable is whether holders choose immediate liquidity or structured distribution.
CONTEXT_TAG: Well-telegraphed event
""",
    
    "heatmap": """ROLE: You are a professional crypto market analyst writing for a US-based, high-signal audience.

INPUT: Crypto Market Heatmap screenshot

TASK: Interpret the overall performance pattern and what it reveals about market structure, breadth, and risk distribution.

RULES:
- Clear, professional American English
- NO price targets, NO financial advice, NO bullish/bearish language
- NO hype, NO emojis, NO hashtags
- Focus on market breadth, sector rotation, and participation patterns
- Use probabilistic language: "historically," "tends to," "often coincides," "may indicate"

OUTPUT FORMAT (MANDATORY):

ALPHA_TAKE: [2-4 sentences explaining what the heatmap pattern reveals about market structure, breadth, and capital distribution]

CONTEXT_TAG: [ONE of: Defensive positioning | Broad weakness | Selective strength | Liquidity contraction | Volatile range | Trend transition phase]

EXAMPLE:
ALPHA_TAKE: Broad-based weakness across mid-caps while large-caps hold suggests defensive positioning and liquidity contraction. This setup often persists until either catalysts emerge or capitulation creates asymmetric entry points in quality names. Improved breadth across market cap tiers would be required to signal a meaningful regime shift.
CONTEXT_TAG: Defensive positioning
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
        
        # Извлекаем ALPHA_TAKE и CONTEXT_TAG
        alpha_take = None
        context_tag = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('ALPHA_TAKE:'):
                alpha_take = line.replace('ALPHA_TAKE:', '').strip()
            elif line.startswith('CONTEXT_TAG:'):
                context_tag = line.replace('CONTEXT_TAG:', '').strip()
        
        # Валидация
        if not alpha_take:
            logger.warning(f"Could not parse Alpha Take from response")
            logger.warning(f"  Response: {content}")
            # Fallback: используем весь ответ если нет маркера
            alpha_take = content
        
        logger.info(f"  ✓ Alpha Take: {alpha_take}")
        if context_tag:
            logger.info(f"  ✓ Context Tag: {context_tag}")
        
        return {
            "alpha_take": alpha_take,
            "context_tag": context_tag  # Может быть None
        }
        
    except Exception as e:
        logger.error(f"Error getting Alpha Take: {e}")
        import traceback
        traceback.print_exc()
        return None


def add_alpha_take_to_caption(title, hashtags, ai_result):
    """
    Добавляет Alpha Take к caption с правильным форматированием
    
    Format:
    <title>
    
    Alpha Take
    <alpha_take text>
    
    Context: <context_tag>
    
    <hashtags>
    
    Args:
        title: Заголовок поста
        hashtags: Хештеги
        ai_result: Результат от get_ai_comment() - {"alpha_take": "...", "context_tag": "..."}
        
    Returns:
        str: Caption с Alpha Take
    """
    if not ai_result:
        # Без AI - старый формат (title + hashtags)
        return f"<b>{title}</b>\n\n{hashtags}"
    
    alpha_take = ai_result['alpha_take']
    context_tag = ai_result.get('context_tag')  # Может быть None
    
    # Новый формат: Title -> Alpha Take -> Alpha take text -> Context Tag (if exists) -> Hashtags
    caption = f"<b>{title}</b>\n\n"
    caption += f"<b>Alpha Take</b>\n"
    caption += f"{alpha_take}\n\n"
    
    # Добавляем Context Tag если есть
    if context_tag:
        caption += f"<i>Context: {context_tag}</i>\n\n"
    
    caption += f"{hashtags}"
    
    return caption
