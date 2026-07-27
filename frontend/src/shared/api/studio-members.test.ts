import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@shared/lib/config", () => ({
  config: {
    apiUrl: "https://api.example.com",
    hasBackend: true,
  },
}));

import {
  addStudioMember,
  fetchStudioMembers,
  removeStudioMember,
  updateStudioMember,
} from "./studio-members";
import { setAuthTokenProvider } from "./client";

const memberPayload = {
  id: 11,
  studio_id: 7,
  user_id: 42,
  role: "instructor",
  email: "coach@example.com",
  name: "Coach",
  created_at: "2026-07-01T10:00:00Z",
  updated_at: "2026-07-01T10:00:00Z",
};

describe("studio members API", () => {
  beforeEach(() => {
    setAuthTokenProvider(() => "session-token");
  });

  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("lists members with page and size query params", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [memberPayload],
          total: 1,
          page: 1,
          size: 20,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchStudioMembers(7, { page: 2, size: 10 });

    expect(result.total).toBe(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.com/api/v1/studios/7/members?page=2&size=10",
      expect.objectContaining({
        method: "GET",
      }),
    );
  });

  it("posts add-member payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(memberPayload), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await addStudioMember(7, {
      email: "coach@example.com",
      role: "instructor",
    });

    expect(result.id).toBe(11);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.com/api/v1/studios/7/members",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "coach@example.com",
          role: "instructor",
        }),
      }),
    );
  });

  it("patches member role and deletes member", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ...memberPayload, role: "manager" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    const updated = await updateStudioMember(7, 11, { role: "manager" });
    expect(updated.role).toBe("manager");

    await removeStudioMember(7, 11);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "https://api.example.com/api/v1/studios/7/members/11",
      expect.objectContaining({ method: "PATCH" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "https://api.example.com/api/v1/studios/7/members/11",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
