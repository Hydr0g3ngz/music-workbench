using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using System.Collections.Generic;

class Launcher : Form {
    readonly string root = AppDomain.CurrentDomain.BaseDirectory;
    readonly string logs = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MusicWorkbench", "Logs");
    Process backend;
    string url, workspace, failure;
    bool ready, closing, english, downloadNeeded;
    Label title = new Label(), status = new Label(), hint = new Label();
    Button open = new Button(), folder = new Button(), log = new Button(), retry = new Button(), language = new Button(), quit = new Button();
    public Launcher() {
        Text = "Music Workbench"; ClientSize = new Size(590, 390); MinimumSize = new Size(606, 429);
        StartPosition = FormStartPosition.CenterScreen; BackColor = Color.FromArgb(21,27,35); ForeColor = Color.FromArgb(232,240,245);
        Font = new Font("Microsoft YaHei UI", 10);
        title.SetBounds(30,25,420,42); title.Font = new Font(Font.FontFamily,23,FontStyle.Bold); title.Text="Music Workbench";
        language.SetBounds(464,30,96,32); language.Text="English"; language.Click += delegate {english=!english; Labels();};
        status.SetBounds(32,90,520,52); status.Font=new Font(Font.FontFamily,13);
        hint.SetBounds(32,149,520,70); hint.ForeColor=Color.FromArgb(167,184,197);
        open.SetBounds(32,235,250,48); open.BackColor=Color.FromArgb(114,207,173);open.ForeColor=Color.FromArgb(12,35,30);
        open.Click += delegate {if(downloadNeeded)Process.Start(new ProcessStartInfo("https://github.com/Hydr0g3ngz/music-workbench/releases"){UseShellExecute=true});else OpenApp(false);};
        retry.SetBounds(302,235,250,48);retry.Click += delegate {if(ready) OpenApp(true);else StartBackend();};
        folder.SetBounds(32,307,160,38);folder.Click += delegate {if(workspace!=null) Process.Start("explorer.exe", Quote(workspace));};
        log.SetBounds(211,307,160,38);log.Click += delegate {Directory.CreateDirectory(logs);Process.Start("explorer.exe",Quote(logs));};
        quit.SetBounds(391,307,160,38);quit.Click += delegate {Close();};
        Controls.AddRange(new Control[]{title,language,status,hint,open,retry,folder,log,quit});
        FormClosing += Shutdown; Shown += delegate {StartBackend();}; Labels();
    }
    static string Quote(string value) {return "\""+value.Replace("\"", "")+"\"";}
    void Labels() {
        language.Text=english?"中文":"English";
        status.Text=ready?(english?"Ready — your music stays on this computer.":"已就绪，你的作品保存在这台电脑上。"):
            failure!=null?(english?"Could not start. Open the log or retry.":"启动未完成，可以重试或打开日志。"):
            (english?"Preparing your workspace…":"正在准备你的创作空间…");
        hint.Text=failure??(english?"Start with an editable example, import a recording, or create with local AI.\nClosing the music window keeps this launcher running. Exit here to stop the background service.":"从可编辑示例、自己的录音或本地 AI 开始创作。\n关闭音乐窗口后仍可在这里重新打开；退出启动器会停止它启动的后台服务。");
        open.Text=downloadNeeded?(english?"Download Portable":"下载免安装版"):(english?"Open music workspace":"打开音乐工作台");open.Enabled=ready||downloadNeeded;
        retry.Text=ready?(english?"Open in browser":"在浏览器中打开"):(english?"Retry":"重新启动");
        folder.Text=english?"My project files":"我的作品文件";folder.Enabled=workspace!=null;
        log.Text=english?"Startup logs":"启动日志";quit.Text=english?"Exit launcher":"退出启动器";
    }
    void WriteLog(string text) {try {Directory.CreateDirectory(logs);lock(logs) File.AppendAllText(Path.Combine(logs,"startup.log"),DateTime.Now.ToString("s")+" "+text+Environment.NewLine,Encoding.UTF8);}catch{}}
    void Dispatch(Action action) {if(!closing&&!IsDisposed) try{BeginInvoke(action);}catch{}}
    void StartBackend() {
        try{if(backend!=null&&!backend.HasExited)return;}catch{}
        ready=false;failure=null;downloadNeeded=false;Labels();
        string python=Path.Combine(root,"runtime","python.exe");
        bool portable=File.Exists(python);
        if(!portable)python=Path.Combine(root,".venv-next","Scripts","python.exe");
        if(!File.Exists(python)) {downloadNeeded=true;failure=english?"Download the Windows Portable package from GitHub Releases. The source package needs Python setup.":"请下载 GitHub Releases 中的 Windows Portable 免安装包；源码包需要先配置 Python。";Labels();return;}
        workspace=portable?Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"MusicWorkbench","Projects"):Path.Combine(root,"outputs","workbench");
        var args=Environment.GetCommandLineArgs();
        for(int i=1;i+1<args.Length;i++)if(args[i]=="--workspace")workspace=Path.GetFullPath(args[i+1]);
        var info=new ProcessStartInfo(python,"-X utf8 -m music_studio.desktop --controller --no-browser --workspace "+Quote(workspace));
        info.WorkingDirectory=root;info.UseShellExecute=false;info.CreateNoWindow=true;
        info.RedirectStandardOutput=true;info.RedirectStandardError=true;info.RedirectStandardInput=true;
        info.StandardOutputEncoding=Encoding.UTF8;info.StandardErrorEncoding=Encoding.UTF8;
        info.EnvironmentVariables["PYTHONUTF8"]="1";
        if(!portable)info.EnvironmentVariables["PYTHONPATH"]=Path.Combine(root,"src");
        backend=new Process();backend.StartInfo=info;backend.EnableRaisingEvents=true;
        backend.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) {if(e.Data!=null)WriteLog(e.Data);};
        backend.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) {
            if(e.Data==null)return;WriteLog(e.Data);
            try{var data=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(e.Data);
                Dispatch(delegate {if((string)data["state"]=="ready"){url=(string)data["url"];ready=true;failure=null;Labels();OpenApp(false);}
                else if((string)data["state"]=="error"){failure=(string)data["message"];Labels();}});
            }catch{}
        };
        backend.Exited += delegate {Dispatch(delegate {if(!ready){failure=english?"The background service stopped. See startup.log.":"后台服务未能启动，请查看 startup.log。";Labels();}});};
        try{backend.Start();backend.BeginOutputReadLine();backend.BeginErrorReadLine();}catch(Exception e){failure=e.Message;WriteLog(e.ToString());Labels();}
    }
    void OpenApp(bool browser) {
        if(!ready||url==null)return;
        try {
            if(!browser){
                string edge=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),"Microsoft","Edge","Application","msedge.exe");
                if(File.Exists(edge)){Process.Start(new ProcessStartInfo(edge,"--app="+Quote(url)){UseShellExecute=true});return;}
            }
            Process.Start(new ProcessStartInfo(url){UseShellExecute=true});
        }catch(Exception e){WriteLog(e.ToString());MessageBox.Show(e.Message,"Music Workbench");}
    }
    void Shutdown(object sender,FormClosingEventArgs e) {
        closing=true;
        if(backend==null)return;
        try{if(!backend.HasExited){backend.StandardInput.WriteLine("quit");backend.StandardInput.Flush();
            Hide();if(!backend.WaitForExit(30000))backend.Kill();}}catch{}
    }
    [STAThread] static void Main() {Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new Launcher());}
}
