/* Generic Windows x64 command forwarding only. No Sengoo/application logic.
 * This binary is CRT-free: WindowsApps needs no extra runtime DLL. Both command
 * aliases use the same bytes and follow the installer's owned bin junction.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

static DWORD text_length(const WCHAR *text) {
    DWORD length = 0;
    while (text[length] && length < 32767) ++length;
    return length;
}

static BOOL alias_equal(const WCHAR *actual, const WCHAR *expected) {
    for (;;) {
        WCHAR a = *actual++, b = *expected++;
        if (a >= L'A' && a <= L'Z') a += L'a' - L'A';
        if (a != b) return FALSE;
        if (!a) return TRUE;
    }
}

static BOOL WINAPI console_signal(DWORD signal) {
    /* The real application receives the console signal and owns cleanup. */
    return signal == CTRL_C_EVENT || signal == CTRL_BREAK_EVENT;
}

static void failure(const char *message, DWORD length, DWORD code) {
    DWORD written;
    HANDLE error = GetStdHandle(STD_ERROR_HANDLE);
    if (error && error != INVALID_HANDLE_VALUE)
        WriteFile(error, message, length, &written, NULL);
    ExitProcess(code);
}

void sencode_command_launcher_entry(void) {
    const WCHAR directory[] = L".sencode-cli-bin\\";
    const char failed[] = "Sencode command launcher could not start the installed CLI. Reinstall the CLI package.\r\n";
    HANDLE heap = GetProcessHeap();
    WCHAR *module = HeapAlloc(heap, 0, 32768 * sizeof(WCHAR));
    WCHAR *command = HeapAlloc(heap, 0, 32768 * sizeof(WCHAR));
    if (!module || !command) failure(failed, sizeof(failed) - 1, 126);
    DWORD module_length = GetModuleFileNameW(NULL, module, 32768);
    if (!module_length || module_length >= 32768) failure(failed, sizeof(failed) - 1, 126);
    DWORD basename = module_length;
    while (basename && module[basename - 1] != L'\\' && module[basename - 1] != L'/') --basename;
    if (!alias_equal(module + basename, L"sen.exe") && !alias_equal(module + basename, L"sencode.exe"))
        failure(failed, sizeof(failed) - 1, 126);

    /* Only argv[0] is skipped. The complete raw remainder is copied without
     * interpreting/re-encoding quotes, backslashes, Unicode or metacharacters.
     */
    const WCHAR *tail = GetCommandLineW();
    while (*tail == L' ' || *tail == L'\t') ++tail;
    if (*tail == L'"') {
        ++tail;
        while (*tail && *tail != L'"') ++tail;
        if (*tail) ++tail;
    } else {
        while (*tail && *tail != L' ' && *tail != L'\t') ++tail;
    }
    DWORD alias_length = module_length - basename;
    DWORD directory_length = (DWORD)(sizeof(directory) / sizeof(WCHAR)) - 1;
    DWORD tail_length = text_length(tail);
    DWORD target_length = basename + directory_length + alias_length;
    if (target_length + tail_length + 3 >= 32768) failure(failed, sizeof(failed) - 1, 126);
    DWORD used = 0;
    command[used++] = L'"';
    for (DWORD i = 0; i < basename; ++i) command[used++] = module[i];
    for (DWORD i = 0; i < directory_length; ++i) command[used++] = directory[i];
    for (DWORD i = basename; i < module_length; ++i) command[used++] = module[i];
    command[used++] = L'"';
    for (DWORD i = 0; i < tail_length; ++i) command[used++] = tail[i];
    command[used] = 0;

    STARTUPINFOEXW startup;
    PROCESS_INFORMATION child;
    /* Volatile byte loops keep a compiler from emitting CRT memset calls. */
    volatile BYTE *zero = (volatile BYTE *)&startup;
    for (SIZE_T i = 0; i < sizeof(startup); ++i) zero[i] = 0;
    zero = (volatile BYTE *)&child;
    for (SIZE_T i = 0; i < sizeof(child); ++i) zero[i] = 0;
    startup.StartupInfo.cb = sizeof(startup);
    startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;

    HANDLE inherited[3];
    DWORD inherited_count = 0;
    HANDLE *destinations[] = { &startup.StartupInfo.hStdInput, &startup.StartupInfo.hStdOutput, &startup.StartupInfo.hStdError };
    DWORD identities[] = { STD_INPUT_HANDLE, STD_OUTPUT_HANDLE, STD_ERROR_HANDLE };
    for (DWORD i = 0; i < 3; ++i) {
        HANDLE source = GetStdHandle(identities[i]);
        if (!source || source == INVALID_HANDLE_VALUE) { *destinations[i] = source; continue; }
        if (!DuplicateHandle(GetCurrentProcess(), source, GetCurrentProcess(), destinations[i], 0, TRUE, DUPLICATE_SAME_ACCESS))
            failure(failed, sizeof(failed) - 1, 126);
        inherited[inherited_count++] = *destinations[i];
    }
    SIZE_T attributes_size = 0;
    if (inherited_count) {
        InitializeProcThreadAttributeList(NULL, 1, 0, &attributes_size);
        startup.lpAttributeList = HeapAlloc(heap, 0, attributes_size);
        if (!startup.lpAttributeList || !InitializeProcThreadAttributeList(startup.lpAttributeList, 1, 0, &attributes_size) ||
            !UpdateProcThreadAttribute(startup.lpAttributeList, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
                inherited, inherited_count * sizeof(HANDLE), NULL, NULL))
            failure(failed, sizeof(failed) - 1, 126);
    }
    SetConsoleCtrlHandler(console_signal, TRUE);
    BOOL created = CreateProcessW(NULL, command, NULL, NULL, inherited_count != 0,
        EXTENDED_STARTUPINFO_PRESENT, NULL, NULL, &startup.StartupInfo, &child);
    for (DWORD i = 0; i < inherited_count; ++i) CloseHandle(inherited[i]);
    if (startup.lpAttributeList) {
        DeleteProcThreadAttributeList(startup.lpAttributeList);
        HeapFree(heap, 0, startup.lpAttributeList);
    }
    HeapFree(heap, 0, module);
    HeapFree(heap, 0, command);
    if (!created) failure(failed, sizeof(failed) - 1, 127);
    CloseHandle(child.hThread);
    if (WaitForSingleObject(child.hProcess, INFINITE) != WAIT_OBJECT_0)
        failure(failed, sizeof(failed) - 1, 126);
    DWORD code = 126;
    GetExitCodeProcess(child.hProcess, &code);
    CloseHandle(child.hProcess);
    ExitProcess(code);
}
