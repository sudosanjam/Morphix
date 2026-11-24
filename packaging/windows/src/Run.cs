using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
using System.Net.Sockets;

namespace Morphix
{
    class RunProgram
    {
        static Process serverProcess = null;

        static int Main(string[] args)
        {
            Console.Title = "Morphix - Local Media Engine";
            Console.OutputEncoding = System.Text.Encoding.UTF8;

            string appDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(appDir);

            // Register cleanup on exit / Ctrl+C
            Console.CancelKeyPress += (s, e) =>
            {
                KillServerProcess();
            };
            AppDomain.CurrentDomain.ProcessExit += (s, e) =>
            {
                KillServerProcess();
            };

            PrintBanner();

            string venvPython = Path.Combine(appDir, ".venv", "Scripts", "python.exe");
            if (!File.Exists(venvPython))
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("Virtual environment (.venv) not found. Initializing setup first...\n");
                Console.ResetColor();

                string setupExe = Path.Combine(appDir, "Setup.exe");
                if (File.Exists(setupExe))
                {
                    var p = Process.Start(setupExe);
                    p.WaitForExit();
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine("Error: Setup.exe not found. Please run setup.bat or create .venv.");
                    Console.ResetColor();
                    Console.ReadKey();
                    return 1;
                }

                if (!File.Exists(venvPython))
                {
                    Console.WriteLine("Setup did not complete. Exiting.");
                    Console.ReadKey();
                    return 1;
                }
            }

            if (IsPortListening("127.0.0.1", 7474))
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("  • Morphix is already running on http://127.0.0.1:7474");
                Console.WriteLine("  • Opening web interface in your default browser...\n");
                Console.ResetColor();
                OpenBrowser("http://127.0.0.1:7474");
                Thread.Sleep(1500);
                return 0;
            }

            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("  • Launching Morphix Engine on http://127.0.0.1:7474 ...");
            Console.WriteLine("  • 100% Offline & Private - Zero Cloud Telemetry");
            Console.WriteLine("  • Press Ctrl+C in this window anytime to stop the server.\n");
            Console.ResetColor();

            string runScript = Path.Combine(appDir, "run.py");
            string pyArgs = File.Exists(runScript) ? "run.py" : "-m app.cli.main serve";

            // Launch Python server
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = venvPython,
                Arguments = pyArgs,
                WorkingDirectory = appDir,
                UseShellExecute = false
            };

            try
            {
                serverProcess = Process.Start(psi);
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("Failed to launch Morphix: " + ex.Message);
                Console.ResetColor();
                Console.WriteLine("Press any key to close...");
                Console.ReadKey();
                return 1;
            }

            // Launch browser in a background thread after server is ready
            ThreadPool.QueueUserWorkItem(_ =>
            {
                WaitForPortAndOpenBrowser("127.0.0.1", 7474);
            });

            // Keep alive while server process runs
            serverProcess.WaitForExit();

            // Exit silently — tray quit uses os._exit(0) so exit code is 0.
            // Only show an error if something unexpected crashed.
            if (serverProcess.ExitCode != 0 && serverProcess.ExitCode != -1073741510)
            {
                // -1073741510 = 0xC000013A = Windows CTRL+C/SIGINT — treat as clean exit
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("\nMorphix crashed (exit code: " + serverProcess.ExitCode + ").");
                Console.WriteLine("Check logs for details. Press any key to close.");
                Console.ResetColor();
                Console.ReadKey();
            }

            return 0;
        }

        static bool IsPortListening(string host, int port)
        {
            try
            {
                using (var client = new TcpClient())
                {
                    var result = client.BeginConnect(host, port, null, null);
                    bool success = result.AsyncWaitHandle.WaitOne(300);
                    return success && client.Connected;
                }
            }
            catch { return false; }
        }

        static void OpenBrowser(string url)
        {
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = url,
                    UseShellExecute = true
                });
            }
            catch { }
        }

        static void WaitForPortAndOpenBrowser(string host, int port)
        {
            bool ready = false;
            for (int i = 0; i < 60; i++)
            {
                if (serverProcess != null && serverProcess.HasExited)
                    return;

                Thread.Sleep(300);
                if (IsPortListening(host, port))
                {
                    ready = true;
                    break;
                }
            }

            if (ready)
            {
                OpenBrowser("http://127.0.0.1:" + port);
            }
        }

        static void KillServerProcess()
        {
            try
            {
                if (serverProcess != null && !serverProcess.HasExited)
                {
                    serverProcess.Kill();
                }
            }
            catch { }
        }

        static void PrintBanner()
        {
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine(@"
    __  ___                 __    _      
   /  |/  /___  _________  / /_  (_)_  __
  / /|_/ / __ \/ ___/ __ \/ __ \/ / |/_/
 / /  / / /_/ / /  / /_/ / / / / />  <  
/_/  /_/\____/_/  / .___/_/ /_/_/_/|_|  
                 /_/                    
            ");
            Console.ForegroundColor = ConsoleColor.White;
            Console.WriteLine("   =============================================================");
            Console.WriteLine("             Morphix - Universal Offline Media Transcoder       ");
            Console.WriteLine("   =============================================================");
            Console.ResetColor();
            Console.WriteLine();
        }
    }
}
