# GitHub Actions Setup Instructions

## ⚠️ Important: Manual Setup Required

Due to GitHub OAuth scope restrictions, the workflow file must be added manually through the GitHub web interface.

## Steps to Add the Workflow

1. **Go to your repository:**
   - Visit: https://github.com/SMIC-GCSU/portfolio

2. **Create the workflow file:**
   - Click "Add file" → "Create new file"
   - Path: `.github/workflows/build-release.yml`
   - Copy the entire content from the file in your local repo: `.github/workflows/build-release.yml`

3. **Commit the file:**
   - Add a commit message: "Add GitHub Actions workflow for automated builds"
   - Click "Commit new file"

## What the Workflow Does

The workflow automatically:
- **Builds Windows executable** (.exe) when you push a tag starting with 'v'
- **Builds macOS application** (.app) when you push a tag starting with 'v'
- **Creates a GitHub Release** with both executables
- **Includes transaction.csv** in both builds
- **Adds proper metadata** (publisher, copyright, etc.)

## Creating Your First Release

Once the workflow is added:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will automatically:
1. Build both executables
2. Create a release
3. Upload the files
4. Make them available for download

## Download Links

After the release is created, downloads will be available at:
- Windows: `https://github.com/SMIC-GCSU/portfolio/releases/latest/download/SMIC_Portfolio_Analysis.exe`
- macOS: `https://github.com/SMIC-GCSU/portfolio/releases/latest/download/SMIC_Portfolio_Analysis_macos.zip`

These links are already embedded in the landing page at: https://smic-gcsu.github.io/

