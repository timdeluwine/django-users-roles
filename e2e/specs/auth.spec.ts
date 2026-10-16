import { test, expect } from '@playwright/test';
import { FileManagerPage } from '../pages/FileManagerPage';

test.describe('Авторизация и ограничение доступа', () => {
  test('Анонимный доступ к /files/ перенаправляет на /login/', async ({ page }) => {
    await test.step('Попытка прямого перехода неавторизованным пользователем', async () => {
      await page.goto('/files/');
      await expect(page).toHaveURL(/\/login\/\?next=\/files\//);
    });
  });

  test('Успешный вход и появление навигации файлового менеджера', async ({ page }) => {
    const filePage = new FileManagerPage(page);
    await test.step('Авторизация в системе', async () => {
      await filePage.login('admin', 'password123');
    });

    await test.step('Переход в файловый менеджер по ссылке из шапки', async () => {
      await filePage.navFilesLink.click();
      await expect(page).toHaveURL(/\/files\//);
      await expect(page.getByRole('heading', { name: 'Файловый менеджер' })).toBeVisible();
    });
  });
});