#import "PQPuzzlesStore.h"

static NSString *const kKey = @"puzzlequest.puzzles";

@implementation PQPuzzlesStore

+ (instancetype)sharedStore
{
    static PQPuzzlesStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQPuzzlesStore alloc] init];
    });
    return shared;
}

- (NSInteger)solved
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setSolved:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
