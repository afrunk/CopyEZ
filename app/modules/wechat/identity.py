"""WeChat 账号身份归一

背景：历史上同一个账号被拆成了多行——中文用户名（笨笨 / 蛋蛋）与拼音用户名
（benben / dandan）各占一行。消息分散在不同 id 上：
    id=1 笨笨、id=2 蛋蛋     ← 历史消息都在这里（6721 条）
    id=3 benben、id=4 dandan ← 后来新建的账号，各只有 1 条
于是电脑登录「蛋蛋」能看到全部历史，手机登录「dandan」只看得到一两条。

这里按"人"把账号分组（分组名 = 中文名），消息查询、已读、撤回都按分组处理，
这样任意一台设备登录同一个人名下任意账号，看到的历史记录完全一致。
"""
from app.extensions import db
from app.models.wechat import WeChatUser, WeChatMessage

# 分组名（真实人名）
PERSON_LABELS = ("笨笨", "蛋蛋")

# 拼音用户名 → 分组名
PINYIN_TO_LABEL = {
    "benben": "笨笨",
    "dandan": "蛋蛋",
}


def person_label(user) -> str:
    """返回账号归属的人名（分组名）。

    优先看 display_name，其次看 username；都不是中文名时用拼音映射兜底。
    """
    for candidate in (getattr(user, "display_name", None), getattr(user, "username", None)):
        if candidate in PERSON_LABELS:
            return candidate
    username = (getattr(user, "username", "") or "").strip().lower()
    return PINYIN_TO_LABEL.get(username, getattr(user, "username", "") or "")


def _interaction_count(my_ids: set, other_id: int) -> int:
    """my_ids 这组与某个账号之间的消息条数。"""
    return db.session.query(db.func.count(WeChatMessage.id)).filter(
        db.or_(
            db.and_(
                WeChatMessage.sender_id.in_(my_ids),
                WeChatMessage.receiver_id == other_id,
            ),
            db.and_(
                WeChatMessage.sender_id == other_id,
                WeChatMessage.receiver_id.in_(my_ids),
            ),
        )
    ).scalar() or 0


def resolve_context(user):
    """解析当前用户的会话上下文。

    返回 (my_ids, their_ids, partner)：
      my_ids   —— 属于「我」的账号 id 集合
      their_ids—— 属于「对方」的账号 id 集合
      partner  —— 对方组里的代表账号（用于显示昵称 / 头像 / 在线状态，
                   也作为发消息时的接收方 id）
    """
    users = WeChatUser.query.all()
    my_label = person_label(user)
    my_ids = {u.id for u in users if person_label(u) == my_label}
    if not my_ids:
        my_ids = {user.id}

    # 对方 = 其它分组里与自己互动消息最多的那一组
    other_labels = {}
    for u in users:
        label = person_label(u)
        if label == my_label:
            continue
        other_labels.setdefault(label, []).append(u)

    best_label = None
    best_count = -1
    for label, members in other_labels.items():
        count = sum(_interaction_count(my_ids, m.id) for m in members)
        if count > best_count:
            best_count = count
            best_label = label

    if best_label is None:
        return my_ids, set(), None

    members = other_labels[best_label]
    their_ids = {m.id for m in members}

    # 代表账号：优先选有 display_name 的（显示效果更好），
    # 其次选互动消息最多的。发送消息时用它当 receiver_id，
    # 只要它属于 their_ids，另一端就能正常看到。
    partner = max(
        members,
        key=lambda m: (
            1 if (m.display_name or "").strip() else 0,
            _interaction_count(my_ids, m.id),
        ),
    )
    return my_ids, their_ids, partner
