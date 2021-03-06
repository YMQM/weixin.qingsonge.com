""" 消息关键字回复 """
import time
from app.models import Query, Action
from . import DissCall

diss_call_keywords = ['骚扰电话', '骚扰号码']


def keywords_parser(msg):
    """
    处理关键字命中规则

    :param msg: 解析后的消息字典（用户）
    :return msg: kw业务处理后的消息字典（返回）
    """
    # 获取数据，方便使用
    phone = msg['Content']
    query_id = msg['FromUserName']

    # 查询query
    query = Query.filter_by_id(query_id)

    if query:
        # query存在，优先处理query
        if query.action == 'diss_call':
            # 开始diss_call骚扰，先使用DissCall验证输入的号码
            phone_num = DissCall.check_phone(phone)

            if phone_num:
                # 电话验证通过, 提交骚扰
                if DissCall.start_call(phone_num):
                    # 提交成功

                    expire = query.expire - int(time.time())

                    msg['Content'] = '成功腹黑%s一次，已将其加入DISS骚扰队列。你可在%s秒内继续添加骚扰号码。' % (
                        phone, expire)
                    return msg
                else:
                    # 提交失败
                    msg['Content'] = '腹黑%s失败，请稍后重试！' % phone
                    return msg

            else:
                # 电话验证不通过
                msg['Content'] = '请输入合法的电话号码：'
                return msg
    elif msg['Content'] in diss_call_keywords:
        # query不存在，但命中diss_call关键字
        # 添加diss_call的query, 360s后过期
        action = Action(query_id, 'diss_call', 360)

        # 不在init中触发add，会有诡异问题，单数使用类方法add
        a = Query.save(action)

        # 组织msg
        msg['Content'] = '请添加骚扰过您的电话：'
        return msg
    else:
        # 未命中任何关键字
        if msg['MsgType'] == 'text':
            # 仅当文本类型为text时
            msg['Content'] = '不支持指令：%s。若需腹黑骚扰，请先回复“骚扰号码”或“骚扰电话”触发骚扰指令，然后输入骚扰过你的号码。（千万别拿自己或好友的号码来测试，不对其后果负责）' % msg[
                'Content']
            return msg
        else:
            # 文本类型为event或image等，返回MsgParser处理后的内容
            return msg