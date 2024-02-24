package com.example.huixiangdou;

import android.accessibilityservice.AccessibilityService;
import android.os.Message;
import android.view.accessibility.AccessibilityEvent;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okio.BufferedSink;

public class MyAccessibilityService extends AccessibilityService {

    static final String TAG = MyAccessibilityService.class.getName();
    ExecutorService executor;
    OkHttpClient httpClient;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.i(TAG, "accessibility service created");
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        Log.i(TAG, "accessibility service connected");

        executor = Executors.newSingleThreadExecutor();
        httpClient = new OkHttpClient();
    }

    @Override
    public void onInterrupt() {
        Log.i(TAG, "accessibility service interrupted");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        CharSequence appNameSeq = event.getPackageName();
        if (appNameSeq == null) {
            return;
        }
        if (!appNameSeq.toString().equals("com.tencent.mm")) {
            Log.i(TAG, "ignored package name: " + appNameSeq);
            return;
        }
        Log.i(TAG, "accessibility service listening package name: " + appNameSeq);

        List<CharSequence> dataList = event.getText();
        for (CharSequence ch : dataList) {
            Log.i(TAG, "accessibility service listening app name: " + appNameSeq + ", data: " + ch);
        }
        Log.i(TAG, "handle: " + MyApplication.getApplication().getHandler());
        if (MyApplication.getApplication().getHandler() == null) {
            return;
        }

        for (final CharSequence ch : dataList) {
            if (ch == null) {
                continue;
            }

            String[] list = ch.toString().split(":");
            if (list.length < 2) {
                return;
            }
            Message message = new Message();
            message.what = 0x100;
            message.obj = "消息：" + list[1];
            MyApplication.getApplication().getHandler().sendMessage(message);

            executor.execute(() -> {
                OkHttpClient client = new OkHttpClient().newBuilder()
                        .build();
                MediaType mediaType = MediaType.parse("application/json; charset=utf-8");
                String json =
                        "{" +
                        "  \"messages\": [" +
                        "    {" +
                        "      \"content\": \"" + ch + "\"," +
                        "      \"role\": \"system\"" +
                        "    }" +
                        "  ]," +
                        "  \"model\": \"deepseek-coder\"," +
                        "  \"frequency_penalty\": 0," +
                        "  \"max_tokens\": 2048," +
                        "  \"presence_penalty\": 0," +
                        "  \"stop\": null," +
                        "  \"stream\": false," +
                        "  \"temperature\": 1," +
                        "  \"top_p\": 1" +
                        "}"; // 你的JSON数据
                RequestBody body = RequestBody.create(json, mediaType);
                Request request = new Request.Builder()
                        .url("https://api.deepseek.com/v1/chat/completions")
                        .method("POST", body)
                        .addHeader("Content-Type", "application/json")
                        .addHeader("Accept", "application/json")
                        // 需要在deepseek平台上申请{TOKEN}
                        .addHeader("Authorization", "Bearer TOKEN")
                        .build();
                try {
                    Response response = httpClient.newCall(request).execute();
                    if (!response.isSuccessful()) {
                        Log.e(TAG, "Request failed: " + response.message());
                        return;
                    }
                    if (response.body() == null) {
                        Log.e(TAG, "Request body null.");
                        return;
                    }
                    String responseBody = response.body().string();
                    Log.i(TAG, "accessibility service listening response: " + responseBody);

                    Message message1 = new Message();
                    message1.what = 0x100;
                    message1.obj = "响应: " + responseBody;
                    MyApplication.getApplication().getHandler().sendMessage(message1);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
        }
    }

}
