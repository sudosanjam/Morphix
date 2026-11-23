using System;
using System.IO;
using System.Diagnostics;

namespace Morphix
{
    class UpdateProgram
    {
        static int Main(string[] args)
        {
            Console.Title = "Morphix - One-Click Updater";
            Console.OutputEncoding = System.Text.Encoding.UTF8;

            PrintHeader();

            string appDir = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(appDir);

            // Step 1: Git Status & Pull
            PrintStep(1, "Fetching latest updates from Git repository...");
            int gitExit = RunInteractive("git", "pull origin main", appDir);
            if (gitExit != 0)
            {
                // Fallback attempt plain git pull
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("  Attempting fallback 'git pull'...");
                Console.ResetColor();
                gitExit = RunInteractive("git", "pull", appDir);
            }

            if (gitExit == 0)
            {
                PrintSuccess("Codebase updated to latest commit.");
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.DarkYellow;
                Console.WriteLine("  Notice: Git pull returned code " + gitExit + ". (Are you connected to the internet?)");
                Console.ResetColor();
            }

            // Step 2: Python environment check & dependency sync
            PrintStep(2, "Synchronizing dependencies with requirements.txt...");
            string venvPython = Path.Combine(appDir, ".venv", "Scripts", "python.exe");
            if (File.Exists(venvPython))
            {
                int pipExit = RunInteractive(venvPython, "-m pip install -r requirements.txt", appDir);
                if (pipExit == 0)
                {
                    PrintSuccess("Dependencies up to date.");
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.DarkYellow;
                    Console.WriteLine("  Pip sync completed with warnings.");
                    Console.ResetColor();
                }

                // Step 3: Fast sanity verification
                PrintStep(3, "Running internal self-check verification...");
                int checkExit = RunSilent(venvPython, "-c \"import app; print('Core OK')\"", appDir);
                if (checkExit == 0)
                {
                    PrintSuccess("Morphix core modules verified OK.");
                }
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("  No .venv found. Run Setup.exe to configure your environment.");
                Console.ResetColor();
            }

            Console.WriteLine();
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("===============================================================");
            Console.WriteLine("          [SUCCESS] Morphix Update Check Complete!             ");
            Console.WriteLine("===============================================================");
            Console.ResetColor();
            Console.WriteLine();

            Console.ForegroundColor = ConsoleColor.White;
            Console.Write("Press [ENTER] to launch Morphix, or any other key to close: ");
            var key = Console.ReadKey();
            Console.WriteLine();

            if (key.Key == ConsoleKey.Enter)
            {
                string morphixExe = Path.Combine(appDir, "Morphix.exe");
                if (File.Exists(morphixExe))
                {
                    Process.Start(morphixExe);
                }
                else if (File.Exists(venvPython))
                {
                    Process.Start(venvPython, "run.py");
                }
            }

            return 0;
        }

        static void PrintHeader()
        {
            Console.ForegroundColor = ConsoleColor.Magenta;
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
            Console.WriteLine("              Morphix One-Click Repository & Dep Updater        ");
            Console.WriteLine("   =============================================================");
            Console.ResetColor();
            Console.WriteLine();
        }

        static void PrintStep(int num, string text)
        {
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.Write(" [" + num + "/3] ");
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

        static int RunInteractive(string file, string args, string workingDir)
        {
            try
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
            catch (Exception ex)
            {
                Console.WriteLine("  Command error: " + ex.Message);
                return -1;
            }
        }

        static int RunSilent(string file, string args, string workingDir)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = file,
                    Arguments = args,
                    WorkingDirectory = workingDir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };
                using (var proc = Process.Start(psi))
                {
                    proc.WaitForExit(6000);
                    return proc.ExitCode;
                }
            }
            catch { return -1; }
        }
    }
}
