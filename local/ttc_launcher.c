/* Portable Windows browser-app launcher. No shell or system Python required. */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>

#define PATH_CAPACITY 32768

static int fail(const wchar_t *message, DWORD error)
{
    wchar_t detail[1024];
    if (error)
        swprintf(detail, 1024, L"%ls\n\nWindows error: %lu", message, (unsigned long)error);
    else
        swprintf(detail, 1024, L"%ls", message);
    MessageBoxW(NULL, detail, L"TTC could not start", MB_OK | MB_ICONERROR);
    return 1;
}

static wchar_t *join(const wchar_t *base, const wchar_t *relative)
{
    size_t size = wcslen(base) + wcslen(relative) + 2;
    wchar_t *path = calloc(size, sizeof(wchar_t));
    if (path) swprintf(path, size, L"%ls\\%ls", base, relative);
    return path;
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR arguments, int show)
{
    wchar_t base[PATH_CAPACITY];
    wchar_t *python, *service, *engine, *build, *log, *command;
    SECURITY_ATTRIBUTES security = {sizeof(security), NULL, TRUE};
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    HANDLE output, input, job;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits = {0};
    DWORD length, status = 1, error;
    size_t capacity;
    (void)instance; (void)previous; (void)show;

    length = GetModuleFileNameW(NULL, base, PATH_CAPACITY);
    if (!length || length >= PATH_CAPACITY)
        return fail(L"Cannot locate TTC.exe. Extract the complete package before launching.", GetLastError());
    wchar_t *separator = wcsrchr(base, L'\\');
    if (!separator) return fail(L"Cannot locate the TTC folder.", 0);
    *separator = L'\0';
    python = join(base, L"runtime\\python.exe");
    service = join(base, L"local\\ttc_local.py");
    engine = join(base, L"build\\ttc-cli.exe");
    build = join(base, L"build");
    log = join(base, L"build\\ttc-launch.log");
    if (!python || !service || !engine || !build || !log)
        return fail(L"Not enough memory to start TTC.", 0);
    if (GetFileAttributesW(python) == INVALID_FILE_ATTRIBUTES ||
        GetFileAttributesW(service) == INVALID_FILE_ATTRIBUTES ||
        GetFileAttributesW(engine) == INVALID_FILE_ATTRIBUTES)
        return fail(L"Required TTC files are missing. Extract the complete ZIP and keep TTC.exe beside runtime, local, web, build and licenses.", 0);
    if (!CreateDirectoryW(build, NULL) && GetLastError() != ERROR_ALREADY_EXISTS)
        return fail(L"Cannot create TTC's working folder. Extract the package into a writable location.", GetLastError());
    output = CreateFileW(log, GENERIC_WRITE, FILE_SHARE_READ, &security, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (output == INVALID_HANDLE_VALUE)
        return fail(L"Cannot write build\\ttc-launch.log. Use a writable folder and check whether TTC is already running.", GetLastError());
    input = CreateFileW(L"NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, &security, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (input == INVALID_HANDLE_VALUE) {
        error = GetLastError(); CloseHandle(output);
        return fail(L"Cannot initialize TTC's input handle.", error);
    }
    capacity = wcslen(python) + wcslen(service) + wcslen(engine) + wcslen(arguments) + 80;
    command = calloc(capacity, sizeof(wchar_t));
    if (!command) {
        CloseHandle(input); CloseHandle(output);
        return fail(L"Not enough memory to start TTC.", 0);
    }
    swprintf(command, capacity, L"\"%ls\" -I -B -u \"%ls\" serve --engine \"%ls\" %ls", python, service, engine, arguments);
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = input;
    startup.hStdOutput = output;
    startup.hStdError = output;
    job = CreateJobObjectW(NULL, NULL);
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if (!job || !SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, sizeof(limits))) {
        error = GetLastError(); CloseHandle(input); CloseHandle(output); free(command);
        if (job) CloseHandle(job);
        return fail(L"Cannot initialize TTC's process supervision.", error);
    }
    if (!CreateProcessW(python, command, NULL, NULL, TRUE, CREATE_NO_WINDOW | CREATE_SUSPENDED, NULL, base, &startup, &process)) {
        error = GetLastError(); CloseHandle(input); CloseHandle(output); free(command);
        CloseHandle(job);
        return fail(L"Cannot start the bundled Python runtime. Try extracting the complete package again.", error);
    }
    if (!AssignProcessToJobObject(job, process.hProcess) || ResumeThread(process.hThread) == (DWORD)-1) {
        error = GetLastError(); TerminateProcess(process.hProcess, 1);
        CloseHandle(process.hProcess); CloseHandle(process.hThread); CloseHandle(job);
        CloseHandle(input); CloseHandle(output); free(command);
        return fail(L"Cannot supervise TTC's background process.", error);
    }
    CloseHandle(input); CloseHandle(output); CloseHandle(process.hThread);
    free(command);
    WaitForSingleObject(process.hProcess, INFINITE);
    GetExitCodeProcess(process.hProcess, &status);
    CloseHandle(process.hProcess);
    CloseHandle(job);
    if (status) {
        wchar_t message[1024];
        swprintf(message, 1024, L"TTC stopped unexpectedly (exit code %lu).\n\nDetails are in:\n%ls\n\nYou can also run ttc.cmd serve for visible diagnostics.", (unsigned long)status, log);
        fail(message, 0);
    }
    free(python); free(service); free(engine); free(build); free(log);
    return (int)status;
}
