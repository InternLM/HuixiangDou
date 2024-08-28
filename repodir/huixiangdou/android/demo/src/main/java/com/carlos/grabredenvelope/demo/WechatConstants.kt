package com.carlos.grabredenvelope.demo

import android.util.Log
import com.carlos.cutils.util.LogUtils

/**
 * Created by Carlos on 2019-05-29.
 */
object WechatConstants {

    var RES_ID_GROUP_NAME = "com.tencent.mm:id/obn"   // 群名
    var RES_ID_USER_NAME = "com.tencent.mm:id/brc"    // 发消息的人
    var RES_ID_USER_CONTENT = "com.tencent.mm:id/bkl" // 发的文本内容
    var RES_ID_EDIT_TEXT = "com.tencent.mm:id/bkk"    // 消息输入框
    // 从  8.0.48 开始调整判断逻辑，根据头像坐标定位谁是发送者
    var RES_ID_USER_RL = "com.tencent.mm:id/bn1" // 发消息的 rl
    var RES_ID_USER_HEADER = "com.tencent.mm:id/bk1" // 头像

    fun setVersion(version: String) {
        LogUtils.d("version:$version")
        if (version == "8.0.47" || version == "8.0.48" || version == "8.0.49") {
            RES_ID_GROUP_NAME = "com.tencent.mm:id/obn"
            RES_ID_USER_NAME = "com.tencent.mm:id/brc"
            RES_ID_USER_CONTENT = "com.tencent.mm:id/bkl"
            RES_ID_EDIT_TEXT = "com.tencent.mm:id/bkk"
        } else {
            Log.w("msg", "unknown version, maybe incompatible")
        }
    }
}