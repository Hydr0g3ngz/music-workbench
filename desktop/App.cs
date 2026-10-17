using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

[assembly: TargetFramework(".NETFramework,Version=v4.7.2")]

class WorkbenchWindow : Form {
    readonly string root = AppDomain.CurrentDomain.BaseDirectory;
    readonly string workspace;
    readonly string dataRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MusicWorkbench");
    readonly uint showMessage;
    readonly Label message = new Label();
    readonly Panel loading = new Panel();
    readonly WebView2 view = new WebView2();
    readonly JavaScriptSerializer json = new JavaScriptSerializer();
    readonly object logLock = new object();
    Process backend;
    Uri origin;
    TaskCompletionSource<bool> closeReply;
    bool ready, backendReady, closing, allowClose, shuttingDown;
    bool english = System.Globalization.CultureInfo.CurrentUICulture.TwoLetterISOLanguageName != "zh";

    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern uint RegisterWindowMessage(string name);
    [DllImport("user32.dll")] static extern bool PostMessage(IntPtr handle,uint msg,IntPtr wParam,IntPtr lParam);
    [DllImport("user32.dll")] static extern IntPtr GetThreadDpiAwarenessContext();
    [DllImport("user32.dll")] static extern int GetAwarenessFromDpiAwarenessContext(IntPtr context);
    [DllImport("user32.dll")] static extern uint GetDpiForWindow(IntPtr handle);
    static string Q(string value) { return "\"" + value.Replace("\"", "") + "\""; }
    static string T(bool en,string zh,string text) { return en ? text : zh; }
    public static string Identity(string workspace) {
        using(var hash=SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(Path.GetFullPath(workspace).ToUpperInvariant()))).Replace("-", "");
    }
    public static void ShowExisting(string id) {PostMessage(new IntPtr(0xffff),RegisterWindowMessage("MusicWorkbench.Show."+id),IntPtr.Zero,IntPtr.Zero);}
    public WorkbenchWindow(string folder, string id) {
        workspace=folder;showMessage=RegisterWindowMessage("MusicWorkbench.Show."+id);
        AutoScaleDimensions=new SizeF(96,96);AutoScaleMode=AutoScaleMode.Dpi;
        Text="Music Workbench";ClientSize=new Size(1440,930);MinimumSize=new Size(960,640);
        StartPosition=FormStartPosition.CenterScreen;BackColor=Color.FromArgb(18,25,31);
        Font=new Font("Microsoft YaHei UI",10);
        try {Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath);}catch{}
        var menu=new MenuStrip {BackColor=Color.FromArgb(26,36,43),ForeColor=Color.FromArgb(230,240,240)};
        var home=new ToolStripMenuItem(T(english,"首页","Home"));home.Click+=delegate {if(ready)view.CoreWebView2.Navigate(origin+"welcome.html");};
        var files=new ToolStripMenuItem(T(english,"作品文件","Project files"));files.Click+=delegate {Directory.CreateDirectory(workspace);Process.Start("explorer.exe",Q(workspace));};
        var logs=new ToolStripMenuItem(T(english,"日志","Logs"));logs.Click+=delegate {Directory.CreateDirectory(Path.Combine(dataRoot,"Logs"));Process.Start("explorer.exe",Q(Path.Combine(dataRoot,"Logs")));};
        var reload=new ToolStripMenuItem(T(english,"重新连接","Reconnect"));reload.Click+=delegate {if(ready)view.CoreWebView2.Reload();else StartBackend();};
        var display=new ToolStripMenuItem(T(english,"显示设置","Display"));
        var reset=new ToolStripMenuItem(T(english,"恢复 100% 页面缩放","Reset page zoom to 100%"));reset.Click+=delegate {if(ready)view.ZoomFactor=1;};
        var info=new ToolStripMenuItem(T(english,"显示清晰度信息","Display diagnostics"));info.Click+=async delegate {
            string pixels=ready?await view.CoreWebView2.ExecuteScriptAsync("JSON.stringify({devicePixelRatio:devicePixelRatio,width:innerWidth,height:innerHeight})"):"loading";
            string detail="DPI: "+GetDpiForWindow(Handle)+" / awareness: "+GetAwarenessFromDpiAwarenessContext(GetThreadDpiAwarenessContext())+" (2 = per-monitor)\nZoom: "+view.ZoomFactor+"\n"+pixels;
            Log("Display: "+detail);MessageBox.Show(this,detail,T(english,"显示清晰度","Display diagnostics"));
        };
        display.DropDownItems.AddRange(new ToolStripItem[]{reset,info});
        menu.Items.AddRange(new ToolStripItem[]{home,files,logs,reload,display});MainMenuStrip=menu;
        view.Dock=DockStyle.Fill;view.DefaultBackgroundColor=BackColor;
        loading.Dock=DockStyle.Fill;loading.BackColor=BackColor;
        message.Dock=DockStyle.Fill;message.TextAlign=ContentAlignment.MiddleCenter;
        message.ForeColor=Color.FromArgb(194,216,211);message.Font=new Font(Font.FontFamily,17);
        loading.Controls.Add(message);Controls.Add(view);Controls.Add(loading);Controls.Add(menu);menu.Dock=DockStyle.Top;
        message.Text=T(english,"正在打开你的音乐工作台…","Opening your music workspace…");
        Shown+=delegate {
            var area=Screen.FromControl(this).WorkingArea;
            Size=new Size(Math.Min(Width,area.Width),Math.Min(Height,area.Height));
            Location=new Point(area.Left+(area.Width-Width)/2,area.Top+(area.Height-Height)/2);
            Log("DPI "+GetDpiForWindow(Handle)+"; awareness "+GetAwarenessFromDpiAwarenessContext(GetThreadDpiAwarenessContext()));
            StartBackend();
        };FormClosing+=OnClosing;
    }
    protected override void WndProc(ref Message m) {
        if(m.Msg==showMessage){if(WindowState==FormWindowState.Minimized)WindowState=FormWindowState.Normal;Show();Activate();}
        base.WndProc(ref m);
    }
    void Log(string line) {
        try {Directory.CreateDirectory(Path.Combine(dataRoot,"Logs"));lock(logLock)File.AppendAllText(Path.Combine(dataRoot,"Logs","desktop.log"),DateTime.Now.ToString("s")+" "+line+Environment.NewLine,Encoding.UTF8);}catch{}
    }
    void Dispatch(Action action) {if(!IsDisposed&&!shuttingDown)try{BeginInvoke(action);}catch{}}
    void Fail(string detail) {
        Log(detail);ready=false;loading.Visible=true;loading.BringToFront();
        message.Text=T(english,"暂时无法打开工作台。\n请用顶部‘重新连接’重试，或打开‘日志’。","Could not open the workspace.\nUse Reconnect or open Logs from the menu.");
    }
    void StartBackend() {
        if(closing)return;
        try{if(backend!=null&&!backend.HasExited)return;}catch{}
        string python=Path.Combine(root,"runtime","python.exe");
        if(!File.Exists(python)){Fail("Bundled runtime is missing. Reinstall Music Workbench.");return;}
        backendReady=false;loading.Visible=true;message.Text=T(english,"正在准备创作空间…","Preparing your workspace…");
        var start=new ProcessStartInfo(python,"-X utf8 -m music_studio.desktop --controller --no-browser --workspace "+Q(workspace));
        start.WorkingDirectory=root;start.UseShellExecute=false;start.CreateNoWindow=true;
        start.RedirectStandardInput=true;start.RedirectStandardOutput=true;start.RedirectStandardError=true;
        start.StandardOutputEncoding=Encoding.UTF8;start.StandardErrorEncoding=Encoding.UTF8;
        start.EnvironmentVariables.Remove("PYTHONPATH");start.EnvironmentVariables.Remove("PYTHONHOME");start.EnvironmentVariables["PYTHONUTF8"]="1";
        start.EnvironmentVariables["PYTHONDONTWRITEBYTECODE"]="1";
        backend=new Process {StartInfo=start,EnableRaisingEvents=true};
        backend.ErrorDataReceived+=delegate(object o,DataReceivedEventArgs e){if(e.Data!=null)Log(e.Data);};
        backend.OutputDataReceived+=delegate(object o,DataReceivedEventArgs e){
            if(e.Data==null)return;Log(e.Data);
            try {var state=json.Deserialize<Dictionary<string,object>>(e.Data);
                if((string)state["state"]=="ready"){backendReady=true;Dispatch(delegate {OpenWorkspace((string)state["url"]);});}
                else if((string)state["state"]=="error")Dispatch(delegate {Fail((string)state["message"]);});
            }catch{}
        };
        backend.Exited+=delegate {Dispatch(delegate {if(!backendReady&&!closing)Fail("Backend exited before ready");});};
        try{backend.Start();backend.BeginOutputReadLine();backend.BeginErrorReadLine();}catch(Exception e){Fail(e.ToString());}
    }
    async void OpenWorkspace(string address) {
        if(closing)return;
        try {
            var uri=new Uri(address);
            if(uri.Scheme!="http"||uri.Host!="127.0.0.1")throw new InvalidOperationException("Unexpected local workspace address");
            origin=new Uri(uri.GetLeftPart(UriPartial.Authority)+"/");
            if(view.CoreWebView2==null){
                var profile=Path.Combine(dataRoot,"WebView2");
                var environment=await CoreWebView2Environment.CreateAsync(null,profile);
                await view.EnsureCoreWebView2Async(environment);
                view.CoreWebView2.Settings.IsStatusBarEnabled=false;
                view.CoreWebView2.Settings.AreDefaultContextMenusEnabled=true;
                view.CoreWebView2.NavigationStarting+=delegate(object sender,CoreWebView2NavigationStartingEventArgs e){
                    Uri target;if(!Uri.TryCreate(e.Uri,UriKind.Absolute,out target)||target.Scheme!=origin.Scheme||target.Authority!=origin.Authority)e.Cancel=true;
                };
                view.CoreWebView2.NewWindowRequested+=delegate(object sender,CoreWebView2NewWindowRequestedEventArgs e){
                    e.Handled=true;Uri target;if(e.IsUserInitiated&&Uri.TryCreate(e.Uri,UriKind.Absolute,out target)&&(target.Scheme=="http"||target.Scheme=="https"))Process.Start(new ProcessStartInfo(target.AbsoluteUri){UseShellExecute=true});
                };
                view.CoreWebView2.WebMessageReceived+=delegate(object sender,CoreWebView2WebMessageReceivedEventArgs e){
                    Uri source;if(!Uri.TryCreate(e.Source,UriKind.Absolute,out source)||source.Authority!=origin.Authority)return;
                    try{var reply=json.Deserialize<Dictionary<string,object>>(e.WebMessageAsJson);if((string)reply["type"]=="workbench-close"&&closeReply!=null)closeReply.TrySetResult((bool)reply["saved"]);}catch{}
                };
                view.CoreWebView2.NavigationCompleted+=delegate(object sender,CoreWebView2NavigationCompletedEventArgs e){if(e.IsSuccess){loading.Visible=false;view.Visible=true;}else Fail("WebView navigation failed: "+e.WebErrorStatus);};
                view.CoreWebView2.ProcessFailed+=delegate(object sender,CoreWebView2ProcessFailedEventArgs e){Fail("WebView process failed: "+e.ProcessFailedKind);};
            }
            ready=true;view.CoreWebView2.Navigate(address);
        }catch(Exception error){Fail(error.ToString());}
    }
    async void OnClosing(object sender,FormClosingEventArgs e) {
        if(allowClose)return;
        e.Cancel=true;if(closing)return;closing=true;
        if(ready&&view.CoreWebView2!=null){
            try {
                closeReply=new TaskCompletionSource<bool>();
                await view.CoreWebView2.ExecuteScriptAsync("(function(){var done=function(saved){window.chrome.webview.postMessage({type:'workbench-close',saved:saved});};if(window.WorkbenchDesktop){window.WorkbenchDesktop.prepareClose().then(function(){done(true);},function(){done(false);});}else done(true);})();");
                var completed=await Task.WhenAny(closeReply.Task,Task.Delay(15000));
                if(completed!=closeReply.Task||!closeReply.Task.Result){
                    MessageBox.Show(this,T(english,"还有编辑未能保存。请先恢复连接或导出工程，再退出。","Some edits could not be saved. Reconnect or export the project before exiting."),"Music Workbench");closing=false;return;
                }
            }catch(Exception error){Log(error.ToString());closing=false;return;}
        }
        message.Text=T(english,"正在保存并关闭…","Saving and closing…");loading.Visible=true;loading.BringToFront();
        try{if(backend!=null&&!backend.HasExited){backend.StandardInput.WriteLine("quit");backend.StandardInput.Flush();await Task.Run(()=>{if(!backend.WaitForExit(40000))backend.Kill();});}}catch(Exception error){Log(error.ToString());}
        shuttingDown=true;view.Dispose();allowClose=true;Close();
    }
    [STAThread] static void Main(string[] args) {
        string folder=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"MusicWorkbench","Projects");
        for(int i=0;i+1<args.Length;i++)if(args[i]=="--workspace")folder=Path.GetFullPath(args[i+1]);
        string id=Identity(folder);
        using(var running=new Mutex(false,"MusicWorkbench.Desktop.Running"))
        using(var mutex=new Mutex(false,"Local\\MusicWorkbench.Desktop."+id)){
            bool owns=false;try{owns=mutex.WaitOne(0);}catch(AbandonedMutexException){owns=true;}
            if(!owns){ShowExisting(id);return;}
            try{Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new WorkbenchWindow(folder,id));}finally{mutex.ReleaseMutex();}
        }
    }
}
