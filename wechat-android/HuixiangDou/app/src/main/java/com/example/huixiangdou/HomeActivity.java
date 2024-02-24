package com.example.huixiangdou;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.provider.Settings;
import android.util.Log;
import android.view.View;
import android.widget.TextView;

import androidx.annotation.NonNull;

import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;

import okhttp3.OkHttpClient;

public class HomeActivity extends Activity {

    public static final String TAG = HomeActivity.class.getName();
    private TextView textView;
    private Intent intent;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);

        findViewById(R.id.btn_check).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));
            }
        });
        textView = findViewById(R.id.tv_mm);

        Handler handler = new Handler(this.getMainLooper()) {
            public void handleMessage(@NonNull Message message) {
                Log.i(TAG, "handle msg what: " + message.what);
                if (message.what == 0x100) {
                    textView.append("\n");
                    CharSequence ch = (CharSequence) message.obj;
                    Log.i(TAG, "handle msg info: " + ch);
                    textView.append(ch);
                }
            }
        };
        MyApplication.getApplication().setHandler(handler);

        intent = new Intent(this, MyAccessibilityService.class);
        startService(intent);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        stopService(intent);
    }

}