package com.carlos.grabredenvelope.demo

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Message
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.EditText
import android.widget.TextView
import com.carlos.cutils.util.LogUtils
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_EDIT_TEXT
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_GROUP_NAME
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_USER_CONTENT
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_USER_NAME
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import com.google.gson.Gson
import okhttp3.Call
import okhttp3.Callback
import java.io.IOException
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

data class Query (val type: String, val content: String)
data class UserInfo (val query_id: String, val groupname: String, val username: String, val query: Query)
data class Reply (var code: Int, var reply: String)

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

class SendEmojiService : AccessibilityService() {
    private var myname = "茴香豆"
    private var groupname = ""
    private var lastusername = ""
    private var lastcontent = ""
    private var firststart = 0L
    private var throttle = NoDoubleClick()
    private val WECHAT_PACKAGE = "com.tencent.mm"
    private lateinit var executor: ExecutorService
    private lateinit var httpclient: OkHttpClient
    private var handler = Handler(Looper.getMainLooper())

    override fun onCreate() {
        super.onCreate()
        LogUtils.d("onCreate")
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        LogUtils.d("onServiceConnected")
        httpclient = OkHttpClient()
        executor = Executors.newSingleThreadExecutor();
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

    private fun getAppVersionName(context: Context, packageName: String = context.packageName) = try {
        context.packageManager.getPackageInfo(packageName, 0).versionName
    } catch (e: PackageManager.NameNotFoundException) {
        e.printStackTrace()
        ""
    }

    private fun chat() {

        var userInfo = UserInfo(query_id = "test", groupname = groupname, username = lastusername, Query(type = "text", content = lastcontent))
        var userJsonStr = Gson().toJson(userInfo)

        var helper = SharedPreferenceHelper(applicationContext)
        var url:String? = helper.getString("URL", "")
        var post_url:String = url ?: ""
        executor.execute {
            val client = OkHttpClient()
            // Define the JSON media type
            val JSON :MediaType? = "application/json; charset=utf-8".toMediaTypeOrNull()

            // Create the request body
            val requestBody = userJsonStr.toRequestBody(JSON)

            // Build the request
            val request = Request.Builder()
                .url(post_url)
                .post(requestBody)
                .build()

            client.newCall(request).enqueue(object : Callback{
                override fun onFailure(call: Call, e: IOException) {
                    Log.e("msg", e.toString())
                }

                override fun onResponse(call: Call, response: Response) {
                    handler.post {
                        Log.d("msg resp code", response.code.toString())

                        if (response.isSuccessful) {
                            var reply: String = response.body?.string() ?: "response.body?"
//                            var resp = Gson().fromJson(responseBody.toString(), Reply::class.java)
                            var nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_EDIT_TEXT)
                            if (nodeInfo.size > 0) {
                                for (et in nodeInfo) {
                                    if (et.className == EditText::class.java.name) {
                                        var args = Bundle()
                                        args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, reply)
                                        et.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
                                        Thread.sleep(1000)

                                        var do_send = send()
                                        Log.d("msg", "action send?")
                                        Log.d("msg", do_send.toString())
                                    }
                                }

                            }
                        } else {
                            Log.e("msg", response.toString())
                        }
                    }
                }
            })
        }
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
        var sender_idx = nodeInfo.size - 1
        if (tv.className == TextView::class.java.name) {
            var username = tv.text.toString()
            if (!lastusername.equals(username)) {
                lastusername = username
                send = true
            }
        }

        nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_USER_CONTENT)
        if (nodeInfo.size <= sender_idx) {
            Log.d("msg", "sender count and content count dismatch")
            return
        }
        tv = nodeInfo[sender_idx]
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
            chat()
        }
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