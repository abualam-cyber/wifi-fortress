#!/bin/bash
REPO="yourusername/wifi-fortress"
VERSION="v1.0.7"
RELEASE_NAME="WiFi Fortress v1.0.7"
DESCRIPTION="Stable release with fixed absolute imports and working .deb installer."

git tag $VERSION
git push origin $VERSION

gh release create $VERSION \
  --title "$RELEASE_NAME" \
  --notes "$DESCRIPTION" \
  wifi-fortress_1.0.7_all.deb \
  WiFi_Fortress_User_Guide.pdf \
  WiFi_Fortress_Admin_Guide.pdf
