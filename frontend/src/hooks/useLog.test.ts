import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useLog } from "@/hooks/useLog";

describe("useLog", () => {
  it("keeps only the last 200 lines with unique ids", () => {
    const { result } = renderHook(() => useLog());
    act(() => {
      for (let i = 0; i < 250; i++) result.current.log("info", `linea ${i}`);
    });
    const { logs } = result.current;
    expect(logs).toHaveLength(200);
    expect(logs[0].text).toBe("linea 50");
    expect(logs[199].text).toBe("linea 249");
    expect(new Set(logs.map((l) => l.id)).size).toBe(200);
  });

  it("clear", () => {
    const { result } = renderHook(() => useLog());
    act(() => result.current.log("ok", "x"));
    act(() => result.current.clearLogs());
    expect(result.current.logs).toEqual([]);
  });
});
