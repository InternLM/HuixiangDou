package com.carlos.grabredenvelope.demo

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.EditText
import android.widget.TextView
import com.carlos.cutils.util.LogUtils
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_EDIT_TEXT
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_GROUP_NAME
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_USER_NAME
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_USER_CONTENT
import okhttp3.OkHttpClient


class NoDoubleClick {
    var time = 0L

    fun pass(): Boolean {
        var now = System.currentTimeMillis()
        if (time == 0L) {
            time = now
            return true
        }

        if (now - time > 1000) {
            time = now
            return true
        }
        return false
    }
}

/**
 * Created by Carlos on 2021/2/8.
 * 自动发送表情脚本, 基于微信8.0.47
 */
class SendEmojiService : AccessibilityService() {
    private var myname = "茴香豆"
    private var groupname = ""
    private var lastusername = ""
    private var lastcontent = ""
    private var firststart = 0L
    private var throttle = NoDoubleClick()
    private val WECHAT_PACKAGE = "com.tencent.mm"
    private var httpClient = OkHttpClient()


    override fun onCreate() {
        super.onCreate()
        LogUtils.d("onCreate")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        WechatConstants.setVersion(getAppVersionName(baseContext, WECHAT_PACKAGE))

        when (event.eventType) {
            AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED -> {
                LogUtils.d("通知改变:$event")
            }
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                LogUtils.d("界面改变:$event")
            }
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> {
                LogUtils.d("内容改变:$event")
                // extract latest event in framelayout
                parseSendMessage(event)
            }
        }
    }

    fun getAppVersionName(context: Context, packageName: String = context.packageName) = try {
        context.packageManager.getPackageInfo(packageName, 0).versionName
    } catch (e: PackageManager.NameNotFoundException) {
        e.printStackTrace()
        ""
    }

    private fun parseSendMessage(event: AccessibilityEvent) {
        var classname = event.className.toString()
        var packagename = event.packageName.toString()
        if (classname != "android.widget.LinearLayout" && classname != "android.widget.FrameLayout") return
        if (packagename != "com.tencent.mm") return

        if (firststart == 0L) {
            firststart = System.currentTimeMillis()
            return
        }
        if (System.currentTimeMillis() - firststart < 1000 * 5) {
            Log.d("msg", "skip first start time + 5s")
            return
        }

        // fetch group name
        var nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_GROUP_NAME)
        for (tv in nodeInfo) {
            if (tv.className == TextView::class.java.name) {
                var content = tv.text.toString()
                groupname = content
                break
            }
        }

        // fetch all messages
        nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_USER_NAME)
        if (nodeInfo.size < 1) {
            Log.d("msg", "residUsername not found, return")
            return
        }
        var send = false
        var tv = nodeInfo.last()
        if (tv.className == TextView::class.java.name) {
            var username = tv.text.toString()
            if (!lastusername.equals(username)) {
                lastusername = username
                send = true
            }
        }

        nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_USER_CONTENT)
        tv = nodeInfo.last()
        if (tv.className == TextView::class.java.name) {
            var content = tv.text.toString()
            if (!lastcontent.equals(content)) {
                lastcontent = content
                send = true
            }
        }

        Log.d("msg", groupname)
        Log.d("msg", lastusername)
        Log.d("msg", lastcontent)

        if (lastusername.equals(myname)) {
            send = false
        }
        Log.d("msg", send.toString())
        if (send) {
            nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_EDIT_TEXT)
            if (nodeInfo.size > 0) {
                for (et in nodeInfo) {
                    if (et.className == EditText::class.java.name) {
                        var args = Bundle()
                        args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, lastcontent)
                        et.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
                        Thread.sleep(1000)

                        var do_send = send()
                        Log.d("msg", "action send?")
                        Log.d("msg", do_send.toString())
                    }
                }

            }
        }

//        val accessibilityNodeInfo =
//            rootInActiveWindow?.findAccessibilityNodeInfosByViewId("com.tencent.mm:id/auj")
//                ?: return
//
//        for (editText in accessibilityNodeInfo) {
//            if (editText.className == EditText::class.java.name) {
//                val arguments = Bundle()
//                arguments.putCharSequence(
//                    AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,
//                    "[烟花]"
//                )
//                editText.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
//
//                send()
//                break
//
//            }
//
//        }
    }

    private fun send(): Boolean {
        if (!throttle.pass()) {
            Log.d("msg", "click too more")
            return false
        }
        var do_send = false
        val accessibilityNodeInfos =
            rootInActiveWindow?.findAccessibilityNodeInfosByText("发送") ?: return false
        for (accessibilityNodeInfo in accessibilityNodeInfos) {
            do_send = true
            accessibilityNodeInfo.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        }
        return do_send
    }


    override fun onInterrupt() {
        LogUtils.d("onInterrupt")
    }

    override fun onDestroy() {
        super.onDestroy()
        LogUtils.d("onDestroy")
    }
}