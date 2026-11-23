using System;
using System.IO;
using System.Diagnostics;
using System.Threading;

namespace Morphix
{
    class SetupProgram
    {
        static int Main(string[] args)
        {
            Console.Title = "Morphix - One-Click Installer & Setup";
            Console.OutputEncoding = System.Text.Encoding.UTF8;

            PrintHeader();

            string appDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(appDir);

            // Step 1: Detect Python
            PrintStep(1, "Detecting Python installation...");
            string pythonExe = DetectPython();
            if (string.IsNullOrEmpty(pythonExe))
            {
                PrintError("Python 3.10+ was not found on your system PATH.");
                Console.WriteLine();
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("Please download and install Python from https://www.python.org/downloads/");
                Console.WriteLine("Make sure to check: [x] Add Python to PATH during installation.");
                Console.ResetColor();
                Console.WriteLine();
                Console.Write("Press any key to open python.org in browser...");
                Console.ReadKey();
                try { Process.Start("https://www.python.org/downloads/"); } catch { }
                return 1;
            }
            PrintSuccess("Found Python: " + pythonExe);

            // Step 2: Virtual Environment
            PrintStep(2, "Configuring local virtual environment (.venv)...");
            string venvDir = Path.Combine(appDir, ".venv");
            string venvPython = Path.Combine(venvDir, "Scripts", "python.exe");

            if (!File.Exists(venvPython))
            {
                Console.ForegroundColor = ConsoleColor.DarkGray;
                Console.WriteLine("  Creating virtual environment at .venv ...");
                Console.ResetColor();
                int venvExit = RunCommand(pythonExe, "-m venv .venv", appDir);
                if (venvExit != 0 || !File.Exists(venvPython))
                {
                    PrintError("Failed to create Python virtual environment.");
                    Pause();
                    return 1;
                }
            }
            PrintSuccess("Virtual environment ready at " + venvDir);

            // Step 3: Install Dependencies
            PrintStep(3, "Installing and verifying dependencies from requirements.txt...");
            string reqFile = Path.Combine(appDir, "requirements.txt");
            if (File.Exists(reqFile))
            {
                Console.ForegroundColor = ConsoleColor.DarkGray;
                Console.WriteLine("  Upgrading pip package manager...");
                RunCommand(venvPython, "-m pip install --upgrade pip", appDir);

                Console.WriteLine("  Installing Morphix requirements (FastAPI, PyPDFium2, Pillow, etc.)...");
                Console.ResetColor();
                int pipExit = RunCommand(venvPython, "-m pip install -r requirements.txt", appDir);
                if (pipExit != 0)
                {
                    PrintError("Failed to install some dependencies. Please check your internet connection.");
                    Pause();
                    return 1;
                }
            }
            PrintSuccess("All application dependencies installed and verified.");

            // Step 4: Create Desktop & Start Menu Shortcuts
            PrintStep(4, "Creating desktop launcher shortcut...");
            try
            {
                CreateDesktopShortcut(appDir);
                PrintSuccess("Desktop shortcut 'Morphix' created.");
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.DarkYellow;
                Console.WriteLine("  Notice: Shortcut creation skipped (" + ex.Message + ")");
                Console.ResetColor();
            }

            // Step 5: Finished
            Console.WriteLine();
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("===============================================================");
            Console.WriteLine("       [SUCCESS] Morphix Setup Completed Successfully!         ");
            Console.WriteLine("===============================================================");
            Console.ResetColor();
            Console.WriteLine();
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("  • Morphix is 100% offline, local-only, and ready to use.");
            Console.WriteLine("  • Double-click Morphix.exe or your desktop shortcut anytime.");
            Console.ResetColor();
            Console.WriteLine();

            Console.ForegroundColor = ConsoleColor.White;
            Console.Write("Press [ENTER] to launch Morphix now (or any other key to exit): ");
            var key = Console.ReadKey();
            Console.WriteLine();

            if (key.Key == ConsoleKey.Enter)
            {
                string morphixExe = Path.Combine(appDir, "Morphix.exe");
                if (File.Exists(morphixExe))
                {
                    Process.Start(morphixExe);
                }
                else
                {
                    Process.Start(venvPython, "run.py");
                }
            }

            return 0;
        }

        static void PrintHeader()
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
            Console.WriteLine("           Morphix One-Click Installer & Environment Setup      ");
            Console.WriteLine("   =============================================================");
            Console.ResetColor();
            Console.WriteLine();
        }

        static void PrintStep(int num, string text)
        {
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.Write(" [" + num + "/4] ");
            Console.ForegroundColor = ConsoleColor.White;
            Console.WriteLine(text);
            Console.ResetColor();
        }

        static void PrintSuccess(string text)
        {
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("       [✓] " + text);
            Console.ResetColor();
            Console.WriteLine();
        }

        static void PrintError(string text)
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine("       [X] " + text);
            Console.ResetColor();
        }

        static void Pause()
        {
            Console.WriteLine();
            Console.WriteLine("Press any key to exit...");
            Console.ReadKey();
        }

        static string DetectPython()
        {
            string[] candidates = { "python", "py", "python3" };
            foreach (var cmd in candidates)
            {
                try
                {
                    ProcessStartInfo psi = new ProcessStartInfo
                    {
                        FileName = cmd,
                        Arguments = "--version",
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        UseShellExecute = false,
                        CreateNoWindow = true
                    };
                    using (var proc = Process.Start(psi))
                    {
                        proc.WaitForExit(3000);
                        if (proc.ExitCode == 0)
                        {
                            return cmd;
                        }
                    }
                }
                catch { }
            }

            // Check standard Windows Python paths
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string pyDir = Path.Combine(localAppData, "Programs", "Python");
            if (Directory.Exists(pyDir))
            {
                foreach (var dir in Directory.GetDirectories(pyDir, "Python*"))
                {
                    string pexe = Path.Combine(dir, "python.exe");
                    if (File.Exists(pexe)) return pexe;
                }
            }

            return null;
        }

        static int RunCommand(string file, string args, string workingDir)
        {
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = file,
                Arguments = args,
                WorkingDirectory = workingDir,
                UseShellExecute = false
            };
            using (var proc = Process.Start(psi))
            {
                proc.WaitForExit();
                return proc.ExitCode;
            }
        }

        static void CreateDesktopShortcut(string appDir)
        {
            string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
            string shortcutPath = Path.Combine(desktop, "Morphix.lnk");
            string targetExe = Path.Combine(appDir, "Morphix.exe");
            string iconPath = Path.Combine(appDir, "packaging", "icons", "morphix.ico");

            if (!File.Exists(iconPath))
            {
                iconPath = Path.Combine(appDir, "app", "web", "assets", "morphix.ico");
            }

            string script = string.Format(
                "$ws = New-Object -ComObject WScript.Shell; " +
                "$s = $ws.CreateShortcut('{0}'); " +
                "$s.TargetPath = '{1}'; " +
                "$s.WorkingDirectory = '{2}'; " +
                "$s.IconLocation = '{3}'; " +
                "$s.Description = 'Morphix - Universal Offline Media Transcoder'; " +
                "$s.Save()",
                shortcutPath.Replace("'", "''"),
                targetExe.Replace("'", "''"),
                appDir.Replace("'", "''"),
                iconPath.Replace("'", "''")
            );

            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = "-NoProfile -ExecutionPolicy Bypass -Command \"" + script + "\"",
                CreateNoWindow = true,
                UseShellExecute = false
            };
            using (var proc = Process.Start(psi))
            {
                proc.WaitForExit(5000);
            }
        }
    }
}
