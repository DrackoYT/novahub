package app.novahub;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.Context;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.URLUtil;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

/**
 * El panel de NovaHub a pantalla completa. Todo se abre dentro (el móvil puede no tener navegador),
 * incluido el inicio de sesión de Cloudflare Access; las descargas van a la carpeta «Descargas».
 */
public class MainActivity extends Activity {
    private WebView web;
    private String home;

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        home = getString(R.string.panel_url);
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#121017"));
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setUserAgentString(s.getUserAgentString() + " NovaHubApp/1.0");

        CookieManager cookies = CookieManager.getInstance();
        cookies.setAcceptCookie(true);
        cookies.setAcceptThirdPartyCookies(web, true);  // Cloudflare Access pone su cookie desde su dominio

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                String scheme = req.getUrl().getScheme();
                return !("https".equals(scheme) || "http".equals(scheme));  // nada de intent:// ni otras apps
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
                if (req.isForMainFrame()) showOffline();
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                CookieManager.getInstance().flush();  // la sesión sobrevive a cerrar la app
            }
        });

        web.setDownloadListener((url, userAgent, disposition, mime, length) -> {
            try {
                DownloadManager.Request r = new DownloadManager.Request(Uri.parse(url));
                r.addRequestHeader("Cookie", CookieManager.getInstance().getCookie(url));
                r.addRequestHeader("User-Agent", userAgent);
                String name = URLUtil.guessFileName(url, disposition, mime);
                r.setTitle(name);
                r.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                r.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
                ((DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE)).enqueue(r);
                Toast.makeText(this, "Descargando " + name, Toast.LENGTH_SHORT).show();
            } catch (Exception e) {
                Toast.makeText(this, "No se pudo descargar: " + e.getMessage(), Toast.LENGTH_LONG).show();
            }
        });

        if (saved != null) web.restoreState(saved);
        else web.loadUrl(home);
    }

    private void showOffline() {
        String html = "<html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head>"
                + "<body style='margin:0;height:100vh;display:grid;place-items:center;background:#121017;color:#e8e4f0;font-family:sans-serif;text-align:center'>"
                + "<div><div style='width:56px;height:56px;margin:0 auto 18px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff,#b89cff 30%,#6a35f0 70%);box-shadow:0 0 28px #7b4dff'></div>"
                + "<h2 style='margin:0 0 8px'>Sin conexión</h2><p style='color:#8f88a0;margin:0 24px 22px'>No se puede llegar al servidor. Comprueba la conexión a internet.</p>"
                + "<a href='" + home + "' style='display:inline-block;padding:12px 22px;border-radius:10px;background:#7b4dff;color:#fff;text-decoration:none;font-weight:600'>Reintentar</a></div></body></html>";
        web.loadDataWithBaseURL(home, html, "text/html", "utf-8", home);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onPause() {
        super.onPause();
        CookieManager.getInstance().flush();
    }
}
