import { test, expect } from '@playwright/test'

const pages = ['/', '/research', '/generate', '/publish', '/orchestrator', '/monitoring', '/intelligence']

for (const p of pages) {
  test(`loads ${p}`, async ({ page }) => {
    await page.goto(p)
    await expect(page).toHaveTitle(/CRAEFTO|Automation|Dashboard/i)
  })
}
