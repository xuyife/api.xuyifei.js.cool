from flask import Flask, jsonify, request
from datetime import datetime
import pytz
import random
import lunardate
import httpx

app = Flask(__name__)

SOLAR_HOLIDAYS = {
    "1-1": {"type": "holiday", "name": "元旦", "message": "元旦快乐！"},
    "4-1": {"type": "holiday", "name": "愚人节", "message": "愚人节快乐！"},
    "10-1": {"type": "holiday", "name": "国庆节", "message": "国庆节快乐！"}
}

MEMORIAL_DAYS = {
    "4-4": {"type": "memorial", "name": "清明节", "message": "🕯️ 缅怀先人，追思感恩。🕯️ 向抗击新冠肺炎疫情牺牲烈士和逝世同胞深切哀悼。"},
    "8-14": {"type": "memorial", "name": "世界慰安妇纪念日", "message": "🕯️ 铭记历史，尊重女性，祈愿和平。"},
    "9-30": {"type": "memorial", "name": "烈士纪念日", "message": "🕯️ 缅怀先烈，致敬英雄。"},
    "12-13": {"type": "memorial", "name": "南京大屠杀死难者国家公祭日", "message": "🕯️ 铭记历史，珍爱和平，勿忘国耻。"},
    "7-7": {"type": "memorial", "name": "七七事变纪念日", "message": "🕯️ 勿忘国耻，吾辈自强。"},
    "9-18": {"type": "memorial", "name": "九一八事变纪念日", "message": "🕯️ 铭记历史，警钟长鸣。"},
    "10-25": {"type": "memorial", "name": "抗美援朝纪念日", "message": "🇨🇳 致敬最可爱的人！"},
    "4-14": {"type": "memorial", "name": "青海玉树地震哀悼日", "message": "🕯️ 深切悼念玉树地震遇难同胞。"},
    "5-12": {"type": "memorial", "name": "四川汶川地震哀悼日", "message": "🕯️ 深切悼念汶川地震遇难同胞。"},
    "8-7": {"type": "memorial", "name": "甘肃舟曲特大泥石流哀悼日", "message": "🕯️ 深切悼念舟曲泥石流遇难同胞。"},
    "9-9": {"type": "memorial", "name": "毛泽东同志逝世日", "message": "🕯️ 深切缅怀伟大领袖毛泽东同志。"}
}

LUNAR_HOLIDAYS = {
    (1, 1): {"name": "春节", "message": "🧧 春节快乐！恭贺新禧，万事如意！"},
    (1, 15): {"name": "元宵节", "message": "🏮 元宵节快乐！团团圆圆，甜甜蜜蜜！"},
    (5, 5): {"name": "端午节", "message": "🐲 端午节安康！粽叶飘香，平安健康！"},
    (7, 7): {"name": "七夕节", "message": "💕 七夕快乐！愿有情人终成眷属！"},
    (8, 15): {"name": "中秋节", "message": "🌕 中秋节快乐！月圆人团圆，阖家幸福！"},
    (9, 9): {"name": "重阳节", "message": "🏔️ 重阳节安康！登高望远，敬老爱老！"},
    (12, 8): {"name": "腊八节", "message": "🥣 腊八节快乐！喝腊八粥，暖身暖心！"},
    (12, 30): {"name": "除夕", "message": "🎆 除夕快乐！辞旧迎新，阖家团圆！"}
}

def get_lunar_holiday(year, month, day):
    try:
        lunar = lunardate.LunarDate.fromSolarDate(year, month, day)
        key = (lunar.month, lunar.day)
        if key in LUNAR_HOLIDAYS:
            return LUNAR_HOLIDAYS[key]
    except:
        pass
    return None

def get_special_day(year, month, day):
    date_key = f"{month}-{day}"
    
    if date_key in MEMORIAL_DAYS:
        return MEMORIAL_DAYS[date_key]
    
    if date_key in SOLAR_HOLIDAYS:
        return SOLAR_HOLIDAYS[date_key]
    
    return None

async def fetch_hitokoto():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://v1.hitokoto.cn/?c=i")
            data = resp.json()
            return {
                "content": data.get("hitokoto", ""),
                "author": data.get("from_who", "佚名"),
                "source": data.get("from", "未知出处")
            }
    except Exception as e:
        fallback_poems = [
            {"content": "山重水复疑无路，柳暗花明又一村。", "author": "陆游", "source": "游山西村"},
            {"content": "长风破浪会有时，直挂云帆济沧海。", "author": "李白", "source": "行路难"},
            {"content": "海内存知己，天涯若比邻。", "author": "王勃", "source": "送杜少府之任蜀州"}
        ]
        return random.choice(fallback_poems)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.now(pytz.timezone('Asia/Shanghai')).isoformat()})

@app.route('/api/tips', methods=['GET', 'OPTIONS'])
async def tips():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 204
    
    china_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(china_tz)
    year, month, day = now.year, now.month, now.day
    
    special = get_special_day(year, month, day)
    if special:
        data = special
    else:
        lunar_holiday = get_lunar_holiday(year, month, day)
        if lunar_holiday:
            data = {
                "type": "holiday",
                "name": lunar_holiday["name"],
                "message": lunar_holiday["message"]
            }
        else:
            poem = await fetch_hitokoto()
            data = {
                "type": "poem",
                "content": poem["content"],
                "author": poem["author"],
                "source": poem["source"]
            }
    
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

app_handler = app