import { expect, test } from "@playwright/test";

test("user can log in and reach dashboard", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("SENTINEL ACCESS")).toBeVisible();

  await page.getByPlaceholder("Enter User ID").fill("admin");
  await page.getByPlaceholder("••••••••").fill("admin");
  await page.getByRole("button", { name: "AUTHENTICATE" }).click();

  await expect(page.getByText("Security Operations Center")).toBeVisible();
});

