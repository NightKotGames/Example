USTRUCT(BlueprintType)
struct FPBR_RVT_Row : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TObjectPtr<UTexture2D> BaseColor;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TObjectPtr<UTexture2D> Normal;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TObjectPtr<UTexture2D> ORM;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TObjectPtr<UTexture2D> Height;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float UV_Scale = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float RoughnessOverride = -1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bUseRVTRead = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bUseRVTWrite = false;
};
