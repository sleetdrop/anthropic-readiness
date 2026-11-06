import { constants } from "node:fs";
import { open } from "node:fs/promises";

export async function readBoundedFile(
  path: string,
  limit: number,
  flags = constants.O_RDONLY | constants.O_NONBLOCK,
): Promise<Buffer> {
  const handle = await open(path, flags);
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size > limit) throw new Error("unreadable_or_oversize_file");
    const buffer = Buffer.alloc(limit + 1);
    let size = 0;
    while (size < buffer.length) {
      const { bytesRead } = await handle.read(buffer, size, buffer.length - size, size);
      if (!bytesRead) break;
      size += bytesRead;
    }
    if (size > limit) throw new Error("unreadable_or_oversize_file");
    return buffer.subarray(0, size);
  } finally {
    await handle.close();
  }
}
