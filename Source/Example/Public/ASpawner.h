// Source/Example/Public/ASpawner.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ASpawner.generated.h"

UCLASS(BlueprintType, Blueprintable)
class EXAMPLE_API ASpawner : public AActor
{
    GENERATED_BODY()

public:
    ASpawner();

    virtual void BeginPlay() override;

    /** ����� ������ ������� */
    UFUNCTION(BlueprintCallable)
    void SpawnObject();

    /** ����� ������� ��� ������ */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings")
    TSubclassOf<AActor> SpawnClass;

    /** ������������� ����� �� ������� */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings")
    bool bMultipleSpawn = false;

    /** �������� ����� �������� */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings", meta = (EditCondition = "bMultipleSpawn", ClampMin = "0.01"))
    float SpawnInterval = 5.0f;

    /** ������������ ���������� �������� */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings", meta = (EditCondition = "bMultipleSpawn", ClampMin = "1"))
    int32 MaxSpawnCount = 5;

    /** ������ �������� ������ */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings", meta = (ClampMin = "0.0"))
    float SpawnRadius = 100.0f;

    /** ������������ �� ������� ����������� */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings")
    bool bAlignToSurface = true;

    /** ������ ������ ����������� */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings", meta = (ClampMin = "0.0"))
    float TraceHeightAbove = 1000.0f;

protected:
    /** ������ ��� ������������� ������ */
    FTimerHandle SpawnTimerHandle;

    /** ������ ���������� �������� */
    UPROPERTY(Transient)
    TArray<TWeakObjectPtr<AActor>> SpawnedActors;

    /** ���������� ����������� */
    UFUNCTION()
    void OnSpawnedActorDestroyed(AActor* DestroyedActor);

    /** ������� ������� �� ������������ */
    void CleanUpDestroyedActors();
};
