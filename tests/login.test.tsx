import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import Login from "@/components/Login";

it("submits credentials after delay and calls onLogin", async () => {
  vi.useFakeTimers();
  const onLogin = vi.fn();

  render(<Login onLogin={onLogin} />);

  fireEvent.change(screen.getByPlaceholderText("Enter User ID"), { target: { value: "admin" } });
  fireEvent.change(screen.getByPlaceholderText("••••••••"), { target: { value: "admin" } });
  fireEvent.click(screen.getByRole("button", { name: /authenticate/i }));

  expect(onLogin).not.toHaveBeenCalled();
  await vi.advanceTimersByTimeAsync(800);
  expect(onLogin).toHaveBeenCalledWith("admin", "admin");
  vi.useRealTimers();
});
