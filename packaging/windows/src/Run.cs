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

            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("  • Launching Morphix Engine on http://127.0.0.1:7474 ...");
            Console.WriteLine("  • 100% Offline & Private - Zero Cloud Telemetry");
            Console.WriteLine("  • Press Ctrl+C in this window anytime to stop the server.\n");
            Console.ResetColor();

            // Launch Python server
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = venvPython,
                Arguments = "run.py",
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
                Console.ReadKey();
                return 1;
            }

            // Launch browser in a background thread after brief warm-up
            ThreadPool.QueueUserWorkItem(_ =>
            {
                WaitForPortAndOpenBrowser("127.0.0.1", 7474);
            });

            // Keep alive while server process runs
            serverProcess.WaitForExit();
            return serverProcess.ExitCode;
        }

        static void WaitForPortAndOpenBrowser(string host, int port)
        {
            bool ready = false;
            for (int i = 0; i < 30; i++)
            {
                Thread.Sleep(400);
                try
                {
                    using (var client = new TcpClient())
                    {
                        var result = client.BeginConnect(host, port, null, null);
                        bool success = result.AsyncWaitHandle.WaitOne(400);
                        if (success && client.Connected)
                        {
                            ready = true;
                            break;
                        }
                    }
                }
                catch { }
            }

            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = "http://127.0.0.1:" + port,
                    UseShellExecute = true
                });
            }
            catch { }
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
