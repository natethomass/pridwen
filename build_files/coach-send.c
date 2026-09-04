/* pridwen-coach-send: the shell hooks' client for the Coach daemon.
 *
 * Usage: pridwen-coach-send '<json line>'
 *
 * Connects to $XDG_RUNTIME_DIR/pridwen/coach.sock, writes the line, then
 * prints whatever the daemon replies within a short window (a hint, or
 * nothing). It is C so that every prompt costs about a millisecond. Any
 * failure is silent: a missing daemon must never slow or break a shell.
 *
 * Built in build_files/build.sh with gcc, which is removed again afterwards.
 */
#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#define REPLY_TIMEOUT_MS 250
#define REPLY_MAX 8192

int main(int argc, char **argv)
{
    if (argc < 2 || argv[1][0] == '\0')
        return 0;

    const char *runtime = getenv("XDG_RUNTIME_DIR");
    if (runtime == NULL || runtime[0] == '\0')
        return 0;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof addr);
    addr.sun_family = AF_UNIX;
    if (snprintf(addr.sun_path, sizeof addr.sun_path, "%s/pridwen/coach.sock", runtime) >= (int)sizeof addr.sun_path)
        return 0;

    int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (fd < 0)
        return 0;
    if (connect(fd, (struct sockaddr *)&addr, sizeof addr) < 0) {
        close(fd);
        return 0;
    }

    size_t len = strlen(argv[1]);
    const char *p = argv[1];
    while (len > 0) {
        ssize_t n = write(fd, p, len);
        if (n < 0) {
            if (errno == EINTR)
                continue;
            close(fd);
            return 0;
        }
        p += n;
        len -= (size_t)n;
    }
    if (write(fd, "\n", 1) < 0) {
        close(fd);
        return 0;
    }
    shutdown(fd, SHUT_WR);

    /* Read the reply until EOF or the timeout. The daemon closes after replying. */
    char buf[REPLY_MAX];
    size_t got = 0;
    for (;;) {
        struct pollfd pfd = { .fd = fd, .events = POLLIN };
        int r = poll(&pfd, 1, REPLY_TIMEOUT_MS);
        if (r <= 0)
            break;
        ssize_t n = read(fd, buf + got, sizeof buf - got);
        if (n <= 0)
            break;
        got += (size_t)n;
        if (got >= sizeof buf)
            break;
    }
    close(fd);
    if (got > 0)
        fwrite(buf, 1, got, stdout);
    return 0;
}
