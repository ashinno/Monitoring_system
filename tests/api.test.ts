import MockAdapter from "axios-mock-adapter";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import API from "@/services/api";

let mock: MockAdapter;

beforeEach(() => {
  mock = new MockAdapter(API);
  localStorage.clear();
});

afterEach(() => {
  mock.restore();
});

it("adds Authorization header when token exists", async () => {
  localStorage.setItem("token", "t");

  mock.onGet("/users/me").reply((config) => {
    expect(config.headers?.Authorization).toBe("Bearer t");
    return [200, { id: "admin" }];
  });

  const res = await API.get("/users/me");
  expect(res.status).toBe(200);
});

it("clears token and redirects on 401", async () => {
  Object.defineProperty(window, "location", {
    value: { href: "" },
    writable: true,
  });
  localStorage.setItem("token", "t");

  mock.onGet("/users/me").reply(401, { detail: "unauthorized" });

  await expect(API.get("/users/me")).rejects.toBeTruthy();
  expect(localStorage.getItem("token")).toBeNull();
  expect(window.location.href).toBe("/");
});

